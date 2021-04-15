import os
import socket
import time

from clock import now_us

from values import frame, frametime


if __name__ == "__main__":
	dest = '192.168.3.2'
	src = '192.168.4.2'
	port = 50000
	# socket.SOCK_STREAM for tcp, socket.SOCK_DGRAM for UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((src, port))
	for _ in range(1600):
		start = now_us()
		s.connect((dest, port))
		ret = s.sendall(frame)
		if ret is not None:
			print(ret)
			exit(1)
		print(f"Sent frame at {now_us()}")
		while (start + frametime < now_us()):
			time.sleep(0.001)

