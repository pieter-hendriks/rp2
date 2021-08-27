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
	while True:
		# Handle the control messages from main()
		if ctrlPipe.poll():
			handleMessages(ctrlPipe)
		# Handle messages over the TCP connection
		s.setblocking(False)
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
		s.setblocking(True)
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
segmentCounts = {}
def udpFn(ctrlPipe: mp.Pipe):
	global receivedAny, frameData
	def doExit():
		global frameData
		writeSegmentArrivalTime(-1, -1, -1)
		writeToFile(frameData)
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

	def writeToFile(frameData):
		#global imgBuffer, imgPrevious
		#if imgPrevious != frameIndex:
		for frameIndex in frameData:
			filename = f"frame_{frameIndex}.jpg"
			segmentCount = segmentCounts[frameIndex]
			with open(config.getImgOutFilename(filename), 'wb') as f:
				for segmentIndex in range(segmentCount):
					if frameData[frameIndex][segmentIndex][1] is not None:
						f.write(frameData[frameIndex][segmentIndex][1])
					else:
						f.write(b'0'*1280)
	# def writeToFile(frameIndex, data):
	# 	filename = f"frame_{frameIndex}.jpg"
	# 	with open(config.getImgOutFilename(filename), 'ab') as f:
	# 		f.write(data)


	def writeOffset(offset):
		with open(config.getLogFileName("ntpoffsets"), 'a') as f:
			f.write(f"{(time.time(), offset)}")
			f.write("\n")

	def writeSegmentArrivalTime(frameid, segmentid, timestamp, size):
		global segmentBuffer, segmentPrevious
		if frameid != segmentPrevious:
			with open(config.getLogFileName('segment_arrivals'), 'a') as f:
				f.write(''.join(segmentBuffer))
			segmentBuffer = []
			segmentPrevious = frameid
		segmentBuffer.append(f"({frameid}, {segmentid}, {timestamp}, {size})\n")


	timeOffset = 0
	def handleMessages(pipe):
		global timeOffset, exitWhenDone
		msg = ctrlPipe.recv()
		# Handle exit
		if msg[:len(config.EXITSTRING)] == config.EXITSTRING:
			print("UDP RECEIVED EXIT")
			doExit()
		elif msg[:len(config.NTPOFFSET)] == config.NTPOFFSET:
			timeOffset = struct.unpack('>d', msg[len(config.NTPOFFSET):])
			writeOffset(timeOffset)
			# Set the timeoffset, which will be used whenever we grab the current time.
			# Hope this will make it so reporting is accurate enough.
		else:
			print(f"Unhandled msg in udp function, receiver: {msg}")

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Create 64 MiB buffer. Hopefully this'll fix the missing arrivals?
	s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 67108860)
	s.setblocking(False)
	s.bind((config.receiver, config.udpport))
	s.connect((config.sender, config.udpport))
	s.send(b"trigger") # Any content works, we just notify sender we're alive
	# without this addition, sender would crash if started first
	# Not a problem when doing things manually, a problem if they have to be started automatically
	# At as close a time together as possible
	# Now sender must be started first, but functionality starts at the same time!

	for i in range(config.loopLength):
		frameData[i] = {}
	while True:
		try:
			# Check for control message
			if ctrlPipe.poll():
				handleMessages(ctrlPipe)
			# Try to receive, will throw socket.timeout if no content
			content = s.recv(1500)

			#print("Receive maybe timeout")
			if not content:
				# TODO: Remove this if it doesn't turn out to be relevant
				print("No content. Mark for testing.")
				continue
			receivedAny = True
			#print("Received content")
			myBytes, segment = content[:struct.calcsize('>III')], content[struct.calcsize('>III'):]
			frameid = struct.unpack('>I', myBytes[:4])[0]
			segmentCount = struct.unpack('>I', myBytes[4:8])[0]
			index = struct.unpack('>I', myBytes[8:12])[0]
			#frameid, segmentCount, index = struct.unpack('>III', myBytes)
			segmentCounts[frameid] = segmentCount
			if len(frameData[frameid]) == 0:
				# Ensure stuff is initialized when required
				for i in range(segmentCount):
					frameData[frameid][i] = None, None
			# For the segment, record arrival time (including ntp offset) + the stuff we received.
			# This should allow us to reconstruct the frames we received at a later stage if so desired
			frameData[frameid][index] = (getTime(timeOffset), segment)
			#print(f"writing segment to file: {segment}")
			# writeToFile(frameid, segment)
			writeSegmentArrivalTime(frameid, index, getTime(timeOffset), len(segment))
			# Record frame reception time
			ctrlPipe.send(config.FRAMERECEIVED + struct.pack('>d', getTime(timeOffset)))
			# Then go back to non-blocking
			s.setblocking(False)
		except KeyboardInterrupt as e:
			# Handle ctrlC
			doExit()
		except socket.timeout as e:
			# Handle socket time outs
			print(f"Received socket.timeout: {e}")
			ermsg = e.args[0]
			if ermsg == 'timed out':
				continue
			else:
				doExit()
				raise e from None
		except socket.error as e:
			# Handle other errors, like no-data on socket recv when socket in non-block mode
			if len(e.args) > 0:
				if e.args[0] == 11:
					if not receivedAny:
						# Notify sender they're allowed to begin sending!
						# This error occurs when sender isn't transmitting yet and we're waiting for data
						s.send(b"trigger")
					if exitWhenDone:
						doExit()
					continue
			else:
				print(f"Socket error: {e}")
				print("Exiting...")
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
