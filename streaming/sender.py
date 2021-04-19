import os
import socket
import time
import matplotlib.pyplot as plt
from values import *
from ntp import ntpserver
import struct
import multiprocessing as mp

def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((sender, tcpport))
	s.connect((receiver, tcpport))
	while True:
		if ctrlPipe.poll():
			msg = ctrlPipe.recv()
			if msg[:len(UDPSENDTIME)] == UDPSENDTIME:
				s.send(TCPFRAMEREPORT + framesize.to_bytes(4, byteorder='big') + msg[len(UDPSENDTIME):])
		else:
			# Poll the socket for messages
			s.setblocking(False)
			try:
				recv = s.recv(4096)
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
	for i in range(loopLength):
		ret = s.sendall(frame)
		ctrlPipe.send(UDPSENDTIME + struct.pack(">d", time.time()))
		if ret is not None:
			print(ret)
			print("Sendall returned non-null value (shown above). Assuming this is an error, sender will exit ungracefully.")
			ctrlPipe.send(exitString)
			exit(1)
		while (time.time() < frameStart + frametime):
			time.sleep(0) # I sure hope this doesn't sleep for far too long.
		print(f"Inter-frame sleep over; off by {time.time() - (frameStart + frametime):.4f} seconds")



if __name__ == "__main__":
	# Create the NTP server process and its communication pipe
	# ntpName = 'NTP server'
	# ntpFnPipe, ntpMainPipe = mp.Pipe()
	# ntpProcess = mp.Process(name=ntpName, target=ntpserver.runServer, args=(ntpFnPipe,))

	# Then the UDP frame sender
	udpName = 'UDP frame sender'
	udpFnPipe, udpMainPipe = mp.Pipe()
	udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe,))

	# And finally tcp reporter
	# tcpName = 'TCP reporting fn'
	# tcpFnPipe, tcpMainPipe = mp.Pipe()
	# tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe,))
	
	# Start the processes
	processes = [(udpProcess, udpMainPipe)] # [(ntpProcess, ntpMainPipe), (udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe)]
	for p in processes:
		p.start()
	
	while True:
		time.sleep(1)
	exit(0)
	fig, ax = plt.subplots()
	ax.set(xlabel='Frame #', ylabel='Latency (ms)', title='Frame transmission latency over 60GHz')
	ax.grid()
	ax.plot([i for i in range(loopLength)], [y - x for x, y in times], label="Observed latency")
	ax.plot([i for i in range(loopLength)], [frametime for _ in range(loopLength)], label="Frametime")
	plt.legend()
	plt.show()