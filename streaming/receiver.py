import os
import socket
import time
from values import framesize, receiver, port, loopLength

if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((receiver, port))
	s.listen(1)
	soc, addr = s.accept()
	for _ in range(loopLength):
		frame = soc.recv(8192)
		while (len(frame) < framesize):
			previous = len(frame)
			frame += soc.recv(framesize - len(frame))
			if (len(frame) == previous):
				raise RuntimeError("Receive timed out")
		soc.sendto(b'ACK', addr)