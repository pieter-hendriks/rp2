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
		frame = soc.recv(framesize)
		print(len(frame[0]))
		while (len(frame) < framesize):
			frame += soc.recv(framesize - len(frame))
		print(f"Received frame at: {time.time()}")
		soc.sendto(b'ACK', addr)
		print(f"Sent ack at: {time.time()}")