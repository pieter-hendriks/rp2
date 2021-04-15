import os
import socket

def getFrame():
	framerate = 80
	datarate = 300000 # in Bytes per second
	framesize = datarate/framerate
	frame = os.urandom(framesize)
	return frame

def main():
	

if __name__ == "__main__":
	main()