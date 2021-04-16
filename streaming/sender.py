import os
import socket
import time
import matplotlib.pyplot as plt
from values import frame, frametime, ackLength, loopLength, sender, receiver, port

if __name__ == "__main__":
	times = []
	# socket.SOCK_STREAM for tcp, socket.SOCK_DGRAM for UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)
	s.bind((sender, port))
	s.connect((receiver, port))
	for i in range(loopLength):
		start = time.time()
		ret = s.sendall(frame)
		sentTime = time.time()
		if ret is not None:
			print(ret)
			exit(1)

		ack = s.recv(ackLength)
		ackTime = time.time()
		times.append((sentTime, ackTime))
		while (start + frametime > time.time()):
			time.sleep(0.001)
		print(i)


		fig, ax = plt.subplots()
		ax.set(xlabel='Frame #', ylabel='Latency (ms)', title='Frame transmission latency over 60GHz')
		ax.grid()
		ax.plot([i for i in range(160)], [y - x for x, y in times], legend="Delay between frame transmission start and ACK reception")
		plt.legend()
		plt.show()