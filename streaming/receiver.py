import os
import socket
import time
from values import framesize, receiver, port, loopLength, framerate

if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((receiver, port))
		s.listen(1)
		total = 0
		soc, addr = s.accept()
		for i in range(loopLength):
			frame = soc.recv(8192)
			# Mark start on first iteration
			if i == 0:
				start = time.time()
			# Ensure we keep .recv()'ing until we've recv()'d the entire frame
			while (len(frame) < framesize):
				frame += soc.recv(framesize - len(frame))
			# Send the ack
			soc.sendto(b'ACK', addr)
			# Add frame to received total size
			total += len(frame)
		# Record end time and output data
		end = time.time()
		print(f"Received {total} bytes of data, over {loopLength} frames.\nThis occured over {float(int(10 * (end - start)) / 10)} seconds (goal time was {float(int(10 * (loopLength/framerate)) / 10)} seconds).")
	finally:
		s.close()