import os
import socket

from values import framesize, receiver, port

if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((receiver, port))
	s.listen(1)
	soc, addr = s.accept()
	for _ in range(loopLength):
		frame = soc.recvmsg(framesize)
		#while (len(frame) < framesize):
		#	frame += soc.recv(framesize - len(frame))
		print(f"Received frame at: {time.time()}")
		soc.sendto(b'ACK', addr)
		print(f"Sent ack at: {time.time()}")