import os
import socket
import time
import matplotlib.pyplot as plot
from values import config
config.createLogDirectories('send_')
from ntp import ntpserver
import struct
import multiprocessing as mp
from helpers import handleSenderInterprocessCommunication as handleInterprocessCommunication

# Don't explicitly define the ntp server fn here, as it's located in the ntp server file.


def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def handleExitCommunication(socket=s):
		print("Sending TCP exit message over socket")
		try:
			socket.sendall(config.EXITSTRING)
		except Exception as e:
			if e.args == (32, "Broken pipe"):
				print("Received broken pipeerror as part of TCP exit communication.")
				print("This may occur if receiver is not started.")
			else:
				raise e from None

	def handleMessages(ctrlPipe: mp.Pipe):
		if ctrlPipe.poll():
			msg = ctrlPipe.recv()
			if msg[:len(config.UDPSENDTIME)] == config.UDPSENDTIME:
				s.send(config.TCPFRAMEREPORT + msg[len(config.UDPSENDTIME):])
			elif msg[:len(config.EXITSTRING)] == config.EXITSTRING:
				print("TCP received exit from main, exiting...")
				# Let the receiver know that we're done
				handleExitCommunication()
				# Then exit. No need to ctrlpipe anyhting since main is aware.
				exit(0)
			else:
				print(f"TCP Function has received the following unhandled pipe message: {msg}")

	s.bind((config.sender, config.tcpport))
	connected = False
	# First, we iterate until we've connected. During this period, we still listen for signals from main fn
	while not connected:
		handleMessages(ctrlPipe)
		try:
			s.connect((config.receiver, config.tcpport))
			connected = True
		except Exception as e:
			# If receiver not up yet, retry, else throw the error
			if e.args != (111, 'Connection refused'):
				handleExitCommunication()
				raise e from None
			else:
				continue
	# Then we handle the actual TCP message exchange when connection is established
	while True:
		handleMessages(ctrlPipe)
		# Poll the socket for messages
		s.setblocking(False)
		try:
			recv = s.recv(4096)
			if (len(recv) > 0):
				print(f"Received message on TCP channel: {recv}")
		except socket.timeout as e:
			if e.args[0] != 'timed out':
				print(f"Encountered unexpected error in tcp fn: {e}")
				handleExitCommunication()
				raise e
		except BlockingIOError as e:
			if e.args == (11, 'Resource temporarily unavailable'):
				continue
			else:
				handleExitCommunication()
				raise e from None
		s.setblocking(True)
		# If neither pipe nor socket has messages, yield thread
		#time.sleep(0.005)



def udpFn(ctrlPipe):
	time.sleep(5)
	def handleControlMessage():
		if ctrlPipe.poll():
			rc = ctrlPipe.recv()
			if rc[:len(config.EXITSTRING)] == config.EXITSTRING:
				print("UDP sender received exit.")
				exit(0)
			else:
				print(f"UDP Sender unhandled message: {rc}")
	
	# socket.SOCK_STREAM for tcp, socket.SOCK_DGRAM for UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((config.sender, config.udpport))
	s.connect((config.receiver, config.udpport))
	for frameIndex in range(config.loopLength):
		handleControlMessage()
		frameStart = time.time()
		framedata = config.getFrameData(frameIndex)
		for total, index, segment in config.getFrameSegments(framedata):
			data = struct.pack('>III', frameIndex, total, index) + segment
			ret = s.send(data)
			#ret = s.send(i.to_bytes(4, byteorder='big') + segmentIndex.to_bytes(4, byteorder='big') + segment)
			if ret != struct.calcsize('>III') + len(segment):
				print("Unexpected error in frame send!")
		frameEnd = time.time()
		ctrlPipe.send(config.UDPSENDTIME + struct.pack(">dd", frameStart, frameEnd))
		while (time.time() < frameStart + config.frametime):
			time.sleep(0.001)
	print("UDP function now sending exit string, loop is over.")
	ctrlPipe.send(config.EXITSTRING)
	print("UDP exiting...")


if __name__ == "__main__":
	# Create the NTP server process and its communication pipe
	ntpName = 'NTP server'
	ntpFnPipe, ntpMainPipe = mp.Pipe()
	ntpProcess = mp.Process(name=ntpName, target=ntpserver.runServer, args=(ntpFnPipe, ))

	# Then the UDP frame sender
	udpName = 'UDP frame sender'
	udpFnPipe, udpMainPipe = mp.Pipe()
	udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe, ))

	# And finally tcp reporter
	tcpName = 'TCP reporting fn'
	tcpFnPipe, tcpMainPipe = mp.Pipe()
	tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe, ))

	# Start the processes
	processes = [(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe),
	             (ntpProcess, ntpMainPipe)]  # [(ntpProcess, ntpMainPipe), (udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe)]
	for p, _ in processes:
		p.start()
	pipes = [p for _, p in processes]
	done = False
	while not done:
		readyPipes = mp.connection.wait(pipes)
		for pipe in readyPipes:
			rc = pipe.recv()
			handleInterprocessCommunication(rc, udpMainPipe, tcpMainPipe, ntpMainPipe)
			if rc == config.EXITSTRING:
				done = True
	print("Join()ing all processes...")
	for p, _ in processes:
		print("Calling join()")
		p.join()
		print("Join completed:", p)
	print("All processes have closed gracefully. Join()'s are completed.")
	print("Main function will now exit.")

	exit(0)
	# fig, ax = plt.subplots()
	# ax.set(xlabel='Frame #', ylabel='Latency (ms)', title='Frame transmission latency over 60GHz')
	# ax.grid()
	# ax.plot([i for i in range(loopLength)], [y - x for x, y in times], label="Observed latency")
	# ax.plot([i for i in range(loopLength)], [frametime for _ in range(loopLength)], label="Frametime")
	# plt.legend()
	# plt.show()