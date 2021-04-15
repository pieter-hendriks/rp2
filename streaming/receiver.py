import os
import socket

from values import framesize
from clock import now_us

if __name__ == "__main__":
	myip = '192.168.3.2'
	port = 50000
	s = socket.socket((socket.AF_INET, socket.SOCK_STREAM))
	s.bind((myip, port))
	for _ in range(1600):
		frame = s.recv(framesize)
		print(f"Received frame at: {now_us()}")