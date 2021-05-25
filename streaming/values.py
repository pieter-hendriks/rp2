from os import urandom as rnd
from math import ceil

lan = True
randomFrameData = False


class Configuration:
	def __init__(self, useLAN, useRandomFrameData):
		self.sender = '192.168.4.2'
		self.receiver = '192.168.3.2'

		if useLAN:
			self.ntpserver = '192.168.1.26'
			self.ntpclient= '192.168.1.8'
		else:
			self.ntpserver = self.sender
			self.ntpclient= self.receiver

		# Frame sending configuration
		if useRandomFrameData:
			# 900 kB per frame@30fps ~= 27000 kBps ~= 216000 kbps ~= 216 mbps
			self.framesize = 900000
			self.__framedata = rnd(self.framesize)
			self.getFrameData = lambda _: self.__framedata
		else:
			self.getFrameData = self.__getFrameData
			self.frameInputDirectory = 'frames'
			self.frameFileNameTemplate = 'frame_#.jpg'
		self.framerate = 30
		self.frametime = 1/self.framerate
		# Amount of frames to send
		self.loopLength = 5
		# How large to make the frame segments
		# Since we have an ethernet connection computer->router we are limited by ethernet MTU of 1500 bytes.
		# We set this value to be comfortably below that limit to be safe.
		self.frameSegmentSize  = 1280


		self.udpport = 50000
		self.tcpport = 50001
		self.ntpport = 50123


		# NTP Configuration
		self.ntpversion = 3
		self.ntpFrequency = 1 # Number of times per second to send ntp request

		# String used for interprocess&interapp communication
		self.EXITSTRING = b'EXIT'
		self.UDPSENDTIME = b'UST'
		self.TCPFRAMEREPORT = b'TFR'
		self.TCPRESCALE = b'TRS'
		self.PARTIALFRAME = b'URP'
		self.WRONGFRAMESIZE = b'UBF'
		self.FRAMERECEIVED = b'URF'
		self.NTPOFFSET = b'NOS'

		self.__loggingDirectory = 'log'
		self.__logFileNameTemplate = '#.log'
		self.firstFrame = False

	def getLogFileName(self, type):
		return f"{self.__loggingDirectory}/{self.__logFileNameTemplate.replace('#', type)}"
	def __getFrameData(self, frameIndex: int):
		with open(f"{self.frameInputDirectory}/{self.frameFileNameTemplate.replace('#', str(frameIndex))}", 'rb') as f:
			# File size should fit within memory to avoid everything breaking
			# But that seems like a reasonable assumption in this case
			data = f.read()
			return data

	def getFrameSegmentCount(self, frameData):
		return ceil(len(frameData) / self.frameSegmentSize)

	def getFrameSegments(self, frameData):
		count = self.getFrameSegmentCount(frameData)
		for i in range(count):
			yield count, i, frameData[i * self.frameSegmentSize: (i+1) * self.frameSegmentSize]
		
	def isFirstFrame(self):
		return self.firstFrame
	def markFrameDone(self):
		self.firstFrame = True



config = Configuration(lan, randomFrameData)