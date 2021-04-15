import os
import socket

from values import framesize
from clock import now_us
from values import receiver, port

if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((receiver, port))
	s.listen(1)
	soc, addr = s.accept()
	for _ in range(loopLength):
		frame = soc.recv(framesize)
		while (len(frame) < framesize):
			frame += soc.recv(framesize - len(frame))
		print(f"Received frame at: {now_us()}")
		soc.sendto(b'ACK', addr)
		print(f"Sent ack at: {now_us()}")