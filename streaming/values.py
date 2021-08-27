import os
from math import ceil
import time
from datetime import datetime
import string
import random

lan = False
randomFrameData = False


class Configuration:
	def __init__(self, useLAN, useRandomFrameData):
		# Amount of frames to send
		self.loopLength = 150

		# IP CONFIG
		self.sender = '192.168.3.2'#'127.0.2.1'
		self.receiver = '192.168.4.2'#'127.0.2.2'

		if useLAN:
			self.ntpserver = '10.1.69.39'
			self.ntpclient= '10.1.75.85'
		else:
			self.ntpserver = self.sender
			self.ntpclient= self.receiver

		# Frame sending configuration
		self.lastFrameIndex = -1
		if useRandomFrameData:
			# 900 kB per frame@30fps ~= 27000 kBps ~= 216000 kbps ~= 216 mbps
			self.framesize = 45000
			self.__framedata = b''
			for _ in range(self.framesize):
				self.__framedata += bytes(random.choice(string.ascii_letters), 'utf-8')
			#self.__framedata = os.urandom(self.framesize)
			self.getFrameData = lambda _: self.__framedata
			self.getFrameSize = lambda _: self.framesize
		else:
			self.getFrameData = self.__getFrameData
			self.getFrameSize = lambda _: len(self.__getFrameData(self.lastFrameIndex))
			self.frameInputDirectory = 'frames'
			self.frameFileNameTemplate = 'frame_#.jpg'
		self.framerate = 12
		self.frametime = 1/self.framerate
		# How large to make the frame segments
		# Since we have an ethernet connection computer->router we are limited by ethernet MTU of 1500 bytes.
		# We set this value to be comfortably below that limit to be safe.
		self.frameSegmentSize  = 1280

		# Port config
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
		# Some output configuration
		self.__loggingDirectory = f'log_{datetime.now().isoformat()}'
		self.__imgOutDir = f'img_{datetime.now().isoformat()}'
		self.__logFileNameTemplate = '#.log'
		self.firstFrame = False
	# Helper functions, probably misplaced, ohwell
	def getLogFileName(self, logfile):
		return f"{self.__loggingDirectory}/{self.__logFileNameTemplate.replace('#', logfile)}"
	def getImgOutFilename(self, img):
		return f"{self.__imgOutDir}/{img}"
	def __getFrameData(self, frameIndex: int):
		assert frameIndex >= 0
		self.lastFrameIndex = frameIndex
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
	def createLogDirectories(self, importer):
		# IMporter should be either 'sender' or 'receiver', is used to distinguish log directories.
		if (not os.path.isdir('log')):
			if os.path.isfile('log'):
				os.remove('log')
			os.mkdir('log')
		self.__loggingDirectory = ''.join(['log/', importer, self.__loggingDirectory])
		self.__imgOutDir = ''.join(['log/', importer, self.__imgOutDir])
		os.mkdir(self.__loggingDirectory)
		if importer == 'recv_':
			os.mkdir(self.__imgOutDir)


config = Configuration(lan, randomFrameData)
