import os
import socket
import time
from values import *
import multiprocessing as mp
import struct
import ntplib
from datetime import datetime
from helpers import handleReceiverInterprocessCommunication as handleInterprocessCommunication
# -------       -------
# | 2.1 | ~~~~~ | 2.2 |
# | 3.1 |       | 4.1 |
# -------       -------
#    |             |
# -------       -------
# | 3.2 |       | 4.2 |
# -------       -------
#
# Receiver should run on 3.2.
# Sender on 4.2
# Sender will also be the NTP server, as it's logical for the non-VR display device to have a more accurate clock.

# client = ntplib.NTPClient()
# offset = 0
# for _ in range(100):
# 	response = client.request('192.168.1.26', port=ntpport, version=3)
# 	print(response.offset)
# 	time.sleep(0.3)


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
				if rc[:len(EXITSTRING)] == EXITSTRING:
					print("NTP received exit string, now exiting...")
					# Got this from main function, so simply exit without any signaling
					exit(0)
				else:
					print(f"NTP received unhandled message: {rc}")
			start = time.time()
			response = client.request(
				ntpserver,
				port=ntpport,
				version=ntpversion
			)
			ctrlPipe.send(f"{NTPOFFSET}{response.offset}")
			time.sleep((1 / ntpFrequency) - (time.time() - start))
		except socket.timeout as e:
			if e.args[0] != 'timed out':
				raise e from None
			else:
				continue  # Just re-do the request is request times out, not much else we can do
				# This may be caused by long delay between start of server and client, or bad connection.
				# In any case, essentially the best thing to do is just re-request the time sync.
		except 


def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((receiver, tcpport))
	def handleMessages(pipe):
		msg = pipe.recv()
		if msg[:len(EXITSTRING)] == EXITSTRING:
			# Main function sent us this - so we don't have to do any signaling, we can just exit.
			print("TCP received exit, now exiting...")
			exit(0)
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
				socket.connect((sender, tcpport))
				connected = True
			except Exception as e:
				if e.args == (111, 'Connection refused'):
					continue
				else:
					raise e from None
				print(e.args)
				pass
	
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
				if recv[:len(EXITSTRING)] == EXITSTRING:
					print("Received TCP exit")
					ctrlPipe.send(EXITSTRING)
					exit(0)
				else:
					print(
							f"Received unhandled message on TCP channel: {recv}"
					)
		except socket.timeout as e:
			if e.args[0] != 'timed out':
				print(f"Encountered unexpected error in tcp fn: {e}")
		except BlockingIOError as e:
			if e.args == (11, 'Resource temporarily unavailable'):
				print("Temp unavailable, waiting for connection to be back...")
				waitForConnection(s)
		s.setblocking(True)
		# If neither pipe nor socket has messages, yield thread
		time.sleep(0.005)


def udpFn(ctrlPipe: mp.Pipe):
	def handleMessages(pipe):
		msg = ctrlPipe.recv()
		# Handle exit
		if msg[:len(EXITSTRING)] == EXITSTRING:
			s.close()
			ctrlPipe.send(EXITSTRING)
			ctrlPipe.close()
			break
		elif msg[:len(NTPOFFSET)] == NTPOFFSET:
			timeOffset = float(msg[len(NTPOFFSET):])
			# Set the timeoffset, which will be used whenever we grab the current time.
			# Hope this will make it so reporting is accurate enough.
		else:
			print(f"Unhandled msg in udp function, receiver: {msg}")

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setblocking(False)
	s.bind((receiver, udpport))
	carryover = None
	while True:
		timeOffset = 0
		try:
			# Check for control message
			if ctrlPipe.poll():
				handleMessages(pipe)
			# Mark in case last segment is dropped
			if carryover is None:
				# Try to receive, will throw socket.timeout if no content
				content = s.recv(1500)
			else:
				content = carryover
				carryover = None
			frameid, index = struct.unpack('>II', content[:8])
			if index != 0:
				print(
				    f"First index received != 0. For frame {frameid}, we dropped packets 0 (inclusive) to {index} (exclusive)."
				)
				ctrlPipe.send(PARTIALFRAME)
			# When we've received anything, block for a bit to receive all parts of the message
			s.setblocking(True)
			s.settimeout(0.5)
			try:
				marked = False
				while True:
					previous = index
					recv = s.recv(1500)
					segmentframeid, index = struct.unpack('>II', recv[:8])
					#print(f"Received part {index} out of {len(frameSegments)} for frame {segmentframeid}")
					if segmentframeid != frameid:
						ctrlPipe.send(PARTIALFRAME)
						carryover = recv
						break
					if index != previous + 1:
						count = index - previous
						# In actual implementation, we probably use some sort of storage to indicate we skip those bytes.
						# And re-use the previous frame's values
						content += bytes(count * frameSegmentSize)
						if not marked:
							print(
							    f"Received partial frame for frameid = {frameid}, segments {previous} -> {index}, exclusive"
							)
							ctrlPipe.send(PARTIALFRAME)
							marked = True
					content += recv[8:]
					if (index == len(frameSegments) - 1):
						break
			except socket.timeout as e:
				# Report error if we encounter one (Packet dropped)
				ctrlPipe.send(PARTIALFRAME)
			print(f"Successfully handled frame id {frameid}")

			# Report error, incorrect frame size received
			if len(content) != framesize:
				ctrlPipe.send(WRONGFRAMESIZE)

			# Record frame reception time
			ctrlPipe.send(FRAMERECEIVED +
			              framesize.to_bytes(4, byteorder='big') +
			              struct.pack('>d', getTime(timeOffset)))
			# Then go back to non-blocking
			s.setblocking(False)
		except KeyboardInterrupt as e:
			# Handle ctrlC
			s.close()
			ctrlPipe.send(EXITSTRING)
			ctrlPipe.close()
			exit(0)
		except socket.timeout as e:
			# Handle socket time outs
			print(f"Received socket.timeout: {e}")
			ermsg = e.args[0]
			if ermsg == 'timed out':
				continue
			else:
				throw e from None
		except socket.error as e:
			# Handle other errors, like no-data on socket recv when socket in non-block mode
			if len(e.args) > 0:
				if e.args[0] == 11:
					continue
			else:
				s.close()
				ctrlPipe.send(EXITSTRING)
				ctrlPipe.close()
				exit(0)


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
		# 		NTP client reports time offset to main process, main process forwards to TCP and UDP.
		# 		Main thread and UDP only exchange exit messages.
		#
		# Process communication: main thread <--EXITONLY--> NTP server
		# 											 main thread <--EXITONLY--> UDP
		# 											 UDP --> TCP (UDP will forward exit message to TCP when received ==> UDP server can't return exit until TCP has successfully exited)

		processes = [(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe),
		             (ntpProcess, ntpMainPipe)]
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
				print(
				    f"Receiver handling message: {rc} (EXITSTRING = {EXITSTRING})"
				)
				handleInterprocessCommunication(rc, udpMainPipe, tcpMainPipe,
				                                ntpMainPipe)
				print(
				    f"Receiver handled message: {rc} (EXITSTRING = {EXITSTRING})"
				)
				if rc == EXITSTRING:
					done = True
	except KeyboardInterrupt:
		# Every process/subprocess receives kb interrupt
		# So we don't manually need to do anything here -they'll finish on their own
		print("MAIN received keyboard interrupt, exiting...")
		print(
		    "No exit signals sent - children will also receive KB interrupt signal."
		)
	print("Main function loop ended, join()ing processes")
	for process, _ in processes:
		process.join()
	print("Successfully joined all processes. Exiting...")
	exit(0)

# def main():
# 	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 	try:
# 		s.bind((receiver, udpport))
# 		s.listen(1)
# 		total = 0
# 		soc, addr = s.accept()
# 		for i in range(loopLength):
# 			frame = soc.recv(8192)
# 			# Mark start on first iteration
# 			if i == 0:
# 				start = time.time()
# 			# Ensure we keep .recv()'ing until we've recv()'d the entire frame
# 			while (len(frame) < framesize):
# 				frame += soc.recv(framesize - len(frame))
# 			# Send the ack
# 			soc.sendto(ackmsg, addr)
# 			# Add frame to received total size
# 			total += len(frame)
# 		# Record end time and output data
# 		end = time.time()
# 		print(f"Received {total} bytes of data, over {loopLength} frames.\nThis occured over {float(int(10 * (end - start)) / 10)} seconds (goal time was {float(int(10 * (loopLength/framerate)) / 10)} seconds).")
# 	finally:
# 		s.close()
