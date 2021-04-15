import os
import socket
import time

from clock import now_us

from values import frame, frametime, ackLength, loopLength
from values import sender, receiver, port

if __name__ == "__main__":
	# socket.SOCK_STREAM for tcp, socket.SOCK_DGRAM for UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)
	s.bind((sender, port))
	s.connect((receiver, port))
	for i in range(loopLength):
		start = now_us()
		ret = s.sendall(frame)
		if ret is not None:
			print(ret)
			exit(1)

		print(f"Sent frame at {now_us()}")
		ack = s.recv(ackLength)
		print(f"Received {ack}")

		while (start + frametime > now_us()):
			time.sleep(0.001)
		print(i)

