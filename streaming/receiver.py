import os
import socket
import time
from values import config
config.createLogDirectories('recv_')
import multiprocessing as mp
import struct
import ntplib
from datetime import datetime
from helpers import handleReceiverInterprocessCommunication as handleInterprocessCommunication
# -------				-------
# | 2.1 | ~~~~~ | 2.2 |
# | 3.1 |				| 4.1 |
# -------				-------
#		 |						 |
# -------				-------
# | 3.2 |				| 4.2 |
# -------				-------
#
# Receiver should run on 3.2.
# Sender on 4.2
# Sender will also be the NTP server, as it's logical for the non-VR display device to have a more accurate clock.

# client = ntplib.NTPClient()
# offset = 0
# for _ in range(100):
#		response = client.request('192.168.1.26', port=ntpport, version=3)
#		print(response.offset)
#		time.sleep(0.3)

def getTime(offset):
	return time.time() + offset


def ntpFn(ctrlPipe: mp.Pipe):
	client = ntplib.NTPClient()
	while True:
		try:
			# Handle control messages from main
			# Ensure this is done before the NTP request, because NTP request can error
			# Which would make this unreachable
			if ctrlPipe.poll():
				rc = ctrlPipe.recv()
				if rc[:len(config.EXITSTRING)] == config.EXITSTRING:
					print("NTP received exit string, now exiting...")
					# Got this from main function, so simply exit without any signaling
					exit(0)
				else:
					print(f"NTP received unhandled message: {rc}")
			start = time.time()
			response = client.request(config.ntpserver, port=config.ntpport, version=config.ntpversion,timeout=1.5)
			ctrlPipe.send(config.NTPOFFSET + struct.pack('>d', response.offset))
			if ((1/config.ntpFrequency) - (time.time() - start) > 0):
				time.sleep((1 / config.ntpFrequency) - (time.time() - start))
		except (socket.timeout, ntplib.NTPException) as e:
			print(f"e type: {type(e)}, args = '{e.args[0]}'")
			if e.args[0] in [
					'timed out',
					f'No response received from {config.ntpserver}.',
			]:
				continue
			else:
				raise e from None
				# Just re-do the request is request times out, not much else we can do
				# This may be caused by long delay between start of server and client, or bad connection.
				# In any case, essentially the best thing to do is just re-request the time sync.


def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((config.receiver, config.tcpport))

	def handleMessages(pipe):
		msg = pipe.recv()
		if msg[:len(config.EXITSTRING)] == config.EXITSTRING:
			# Main function sent us this - so we don't have to do any signaling, we can just exit.
			print("TCP received exit, now exiting...")
			s.close()
			exit(0)
		elif msg[:len(config.NTPOFFSET)] == config.NTPOFFSET:
			# Do nothing here, timestamps are used in UDP fn
			pass
		else:
			print(f"TCP FN receiver, unhandled pipe message: {msg}")

	def waitForConnection(socket, pipe):
		connected = False
		while not connected:
			try:
				# Check control messages first, to ensure we're not supposed to be exiting for example
				if pipe.poll():
					handleMessages(pipe)
				# then try connecting/setting the connection
				socket.connect((config.sender, config.tcpport))
				connected = True
			except Exception as e:
				if e.args == (111, 'Connection refused'):
					continue
				else:
					raise e from None

	waitForConnection(s, ctrlPipe)
	s.settimeout(0.2)
	while True:
		# Handle the control messages from main()
		if ctrlPipe.poll():
			handleMessages(ctrlPipe)
		# Handle messages over the TCP connection
		try:
			recv = s.recv(4096)
			if (len(recv) > 0):
				if recv[:len(config.EXITSTRING)] == config.EXITSTRING:
					print("Received TCP exit")
					ctrlPipe.send(config.EXITSTRING)
					exit(0)
				else:
					print(f"Received unhandled message on TCP channel: {recv}")
		except socket.timeout as e:
			if e.args[0] != 'timed out':
				print(f"Encountered unexpected error in tcp fn: {e}")
		except BlockingIOError as e:
			if e.args == (11, 'Resource temporarily unavailable'):
				continue
			else:
				raise e from None
		# # If neither pipe nor socket has messages, yield thread
		# time.sleep(0)

writeSize = 0
imgBuffer = bytearray()
imgPrevious = 0
segmentBuffer = []
segmentPrevious = 0
receivedAny = False
exitWhenDone = False
frameData = {}
timeOffset = 0
segmentCounts = {}


receivedData = []

def udpFn(ctrlPipe: mp.Pipe):
	global receivedAny, frameData
	def doExit():
		print("RCV UDP doExit at", getTime(timeOffset))
		global frameData
		handleData()
		s.close()
		try:
			ctrlPipe.send(config.EXITSTRING)
		except OSError as e:
			# If it's closed, ignore and move on
			pass
		ctrlPipe.close()
		exit(0)
		# writeToFile(frameData)
		# for key in frameData:
		# 	print(frameData[key])
		# 	print(key)

	def handleData():
		global receivedData, segmentCounts, frameData
		last_frameid, lastSegment = None, -1
		for rdIndex in range(len(receivedData)):
			chunk = receivedData[rdIndex][0]
			if len(chunk) < 16:
				raise 1
			frameid, segmentCount, segmentIndex, segmentSize = struct.unpack('>IIII', chunk[:16])
			if frameid != last_frameid:
				print (f"Handling frame {frameid}")
				last_frameid = frameid
			if (lastSegment + 1 != segmentIndex and last_frameid==frameid) and not (frameid != last_frameid + 1 and segmentIndex == 0):
				print("Segment missing from the received data list.")
				print(f"Handled {last_frameid}:{lastSegment}, then jumped to {frameid}:{segmentIndex}")
			lastSegment = segmentIndex
			segment = chunk[16:-4]
			check = chunk[-4:]
			assert len(segment) + len(check) == segmentSize
			assert check == b'\xff\xff\xff\xff'
			segmentCounts[frameid] = segmentCount
			if len(frameData[frameid]) == 0:
				# Ensure stuff is initialized when required
				for i in range(segmentCount):
					frameData[frameid][i] = None, None
			# For the segment, record arrival time (including ntp offset) + the stuff we received.
			# This should allow us to reconstruct the frames we received at a later stage if so desired
			frameData[frameid][segmentIndex] = (receivedData[rdIndex][1], segment)
			assert segment is not None
			#print(f"writing segment to file: {segment}")
			# writeToFile(frameid, segment)
			writeSegmentArrivalTime(frameid, segmentIndex, receivedData[rdIndex][1], segmentSize)
			# Record frame reception time
		writeToFile(frameData)

	def writeToFile(frameData):
		#global imgBuffer, imgPrevious
		#if imgPrevious != frameIndex:
		for frameIndex in frameData:
			filename = f"frame_{frameIndex}.jpg"
			if frameIndex in segmentCounts:
				segmentCount = segmentCounts[frameIndex]
				with open(config.getImgOutFilename(filename), 'wb') as f:
					for segmentIndex in range(segmentCount):
						if frameData[frameIndex][segmentIndex][1] is not None:
							f.write(frameData[frameIndex][segmentIndex][1])
						else:
							#print(f"Frame {frameIndex} segment {segmentIndex} is None; writing zeroes.")
							if segmentIndex == 0:
								#print("Segment zero; writing FFD8+zeroes")
								f.write(b'\xff\xd8' + b'\0' * 1278)
							elif segmentIndex == segmentCount - 1:
								#print("Segment last; writing zeroes+FFD9")
								f.write(b'\0' * 1278 + b'\xff\xd9')
							else:
								f.write(b'\0'*1280)
			else:
				with open(config.getImgOutFilename(filename), 'w') as f:
					f.write('No segments received for this frame.')
	# def writeToFile(frameIndex, data):
	# 	filename = f"frame_{frameIndex}.jpg"
	# 	with open(config.getImgOutFilename(filename), 'ab') as f:
	# 		f.write(data)


	def writeOffset(offset):
		with open(config.getLogFileName("ntpoffsets"), 'a') as f:
			f.write(f"{(time.time(), offset)} --> {getTime(offset)}")
			f.write("\n")

	def writeSegmentArrivalTime(frameid, segmentid, timestamp, size):
		global segmentBuffer, segmentPrevious
		if frameid != segmentPrevious:
			with open(config.getLogFileName('segment_arrivals'), 'a') as f:
				f.write(''.join(segmentBuffer))
			segmentBuffer = []
			segmentPrevious = frameid
		segmentBuffer.append(f"({frameid}, {segmentid}, {timestamp}, {size})\n")


	def handleMessages(pipe):
		global timeOffset, exitWhenDone
		msg = ctrlPipe.recv()
		# Handle exit
		if msg[:len(config.EXITSTRING)] == config.EXITSTRING:
			print("UDP RECEIVED EXIT")
			doExit()
		elif msg[:len(config.NTPOFFSET)] == config.NTPOFFSET:
			timeOffset = struct.unpack('>d', msg[len(config.NTPOFFSET):])[0]
			writeOffset(timeOffset)
			# Set the timeoffset, which will be used whenever we grab the current time.
			# Hope this will make it so reporting is accurate enough.
		else:
			print(f"Unhandled msg in udp function, receiver: {msg}")

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	s.bind((config.receiver, config.udpport))
	s.connect((config.sender, config.udpport))
	s.send(b"0") # Any content works, we just notify sender we're alive
	recvStart = time.time()
	# without this addition, sender would crash if started first
	# Not a problem when doing things manually, a problem if they have to be started automatically
	# At as close a time together as possible
	# Now sender must be started first, but functionality starts at the same time!
	global frameData
	for i in range(config.loopLength):
		frameData[i] = {}
	s.settimeout(5)
	while True:
		try:
			# Check for control message
			if ctrlPipe.poll():
				handleMessages(ctrlPipe)
			# Put content first so we record time after recv
			# Else our time stamp is wrong
			receivedData.append((s.recv(1300), getTime(timeOffset)))
		except socket.timeout as e:
			print("Assuming send is over...")
			break
		except Exception as e:
			print("Unexpected error in receiving data fn")
			raise e from None
	# Subtract an extra five because the last socket timeout is counted if we don't
	print(f"Receiver receiving everything took {time.time() - recvStart - 5}")
	doExit()

if __name__ == "__main__":
	try:
		# Basic setup of variables
		processes = []
		udpName = 'UDP receiver'
		tcpName = 'TCP reporting'
		ntpName = 'NTP client'
		# Construct pipes for interprocess communication
		udpFnPipe, udpMainPipe = mp.Pipe()
		tcpFnPipe, tcpMainPipe = mp.Pipe()
		ntpFnPipe, ntpMainPipe = mp.Pipe()

		# Create the processes
		udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe, ))
		tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe, ))
		ntpProcess = mp.Process(name=ntpName, target=ntpFn, args=(ntpFnPipe, ))

		# Process comms:
		#			NTP client reports time offset to main process, main process forwards to TCP and UDP.
		#			Main thread and UDP only exchange exit messages.
		#
		# Process communication: main thread <--EXITONLY--> NTP server
		#												 main thread <--EXITONLY--> UDP
		#												 UDP --> TCP (UDP will forward exit message to TCP when received ==> UDP server can't return exit until TCP has successfully exited)

		processes = [(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe), (ntpProcess, ntpMainPipe)]
		# Start them
		udpProcess.start()
		tcpProcess.start()
		ntpProcess.start()
		# Wait until program is over
		pipes = [x for _, x in processes]
		done = False
		while not done:
			readyPipes = mp.connection.wait(pipes)
			for pipe in readyPipes:
				rc = pipe.recv()
				#print(f"Receiver handling message: {rc} (EXITSTRING = {config.EXITSTRING})")
				handleInterprocessCommunication(rc, udpMainPipe, tcpMainPipe, ntpMainPipe)
				#print(f"Receiver handled message: {rc} (EXITSTRING = {config.EXITSTRING})")
				if rc == config.EXITSTRING:
					done = True
	except KeyboardInterrupt:
		# Every process/subprocess receives kb interrupt
		# So we don't manually need to do anything here -they'll finish on their own
		print("MAIN received keyboard interrupt, exiting...")
		print("No exit signals sent - children will also receive KB interrupt signal.")
	print("Main function loop ended, join()ing processes")
	for process, _ in processes:
		process.join()
	print("Successfully joined all processes. Exiting...")
	exit(0)
