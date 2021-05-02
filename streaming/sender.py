import os
import socket
import time
import matplotlib.pyplot as plt
from values import *
from ntp import ntpserver
import struct
import multiprocessing as mp
from helpers import handleSenderInterprocessCommunication as handleInterprocessCommunication

# Don't explicitly define the ntp server fn here, as it's located in the ntp server file.

def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((sender, tcpport))
	connected = False
	while not connected:
		try:
			s.connect((receiver, tcpport))
			connected = True
		except Exception as e:
			# If receiver not up yet, retry, else throw the error
			if e.args != (111, 'Connection refused'):
				raise e from None
			else:
				continue
	while True:
		if ctrlPipe.poll():
			msg = ctrlPipe.recv()
			if msg[:len(UDPSENDTIME)] == UDPSENDTIME:
				s.send(TCPFRAMEREPORT + framesize.to_bytes(4, byteorder='big') + msg[len(UDPSENDTIME):])
			elif msg[:len(EXITSTRING)] == EXITSTRING:
				s.send(EXITSTRING)
				raise KeyboardInterrupt
			else:
				print(f"TCP Function has received the following unhandled pipe message: {msg}")
		else:
			# Poll the socket for messages
			s.setblocking(False)
			try:
				recv = s.recv(4096)
				if (len(recv) > 0):
					print(f"Received message on TCP channel: {recv}")
			except socket.timeout as e:
				if e.args[0] != 'timed out':
					print(f"Encountered unexpected error in tcp fn: {e}")
			s.setblocking(True)
		# If neither pipe nor socket has messages, yield thread
		time.sleep(0.005)

def udpFn(ctrlPipe):
	# socket.SOCK_STREAM for tcp, socket.SOCK_DGRAM for UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((sender, udpport))
	s.connect((receiver, udpport))
	print(framesize)
	for i in range(loopLength):
		frameStart = time.time()
		for segment in range(len(frameSegments)):
			ret = s.send(i.to_bytes(4,byteorder='big') + segment.to_bytes(4, byteorder='big') + frameSegments[segment])
			if ret != 8 + len(frameSegments[segment]):
				print("Unexpected error in frame send!")

		ctrlPipe.send(UDPSENDTIME + struct.pack(">d", time.time()))
		print(f"Process should sleep roughtly {(frameStart + frametime) - time.time():.6f} seconds.")
		while (time.time() < frameStart + frametime):
			time.sleep(0.001) # I sure hope this doesn't sleep for far too long.
		print(f"Inter-frame sleep over; off by {time.time() - (frameStart + frametime):.6f} seconds")
	print ("UDP function now sending exit string, loop is over.")
	ctrlPipe.send(EXITSTRING)
	print ("UDP exiting...")

if __name__ == "__main__":
	# Create the NTP server process and its communication pipe
	ntpName = 'NTP server'
	ntpFnPipe, ntpMainPipe = mp.Pipe()
	ntpProcess = mp.Process(name=ntpName, target=ntpserver.runServer, args=(ntpFnPipe,))

	# Then the UDP frame sender
	udpName = 'UDP frame sender'
	udpFnPipe, udpMainPipe = mp.Pipe()
	udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe,))

	# And finally tcp reporter
	tcpName = 'TCP reporting fn'
	tcpFnPipe, tcpMainPipe = mp.Pipe()
	tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe,))

	# Start the processes
	processes = [(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe), (ntpProcess, ntpMainPipe)] # [(ntpProcess, ntpMainPipe), (udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe)]
	for p, _ in processes:
		p.start()
	pipes = [p for _, p in processes]
	while True:
		readyPipes = mp.connection.wait(pipes)
		for pipe in readyPipes:
			rc = pipe.recv()
			print (f"Pipe message handling: msg = {rc}")
			handleInterprocessCommunication(rc, udpMainPipe, tcpMainPipe, ntpMainPipe)

		for proc, pipe in processes:
			if pipe.poll():
				rc = pipe.recv()
				if rc == EXITSTRING:
					for _, otherPipe in [x for x in processes if x != (proc, pipe)]:
						otherPipe.send(EXITSTRING)
					break
				else:
					print(f"Unexpected pipe message from {proc}: {rc}")
	print("Join()ing all processes...")
	for p, _ in processes:
		p.join()
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