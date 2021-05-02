import os
import socket
import time
from values import *
import multiprocessing as mp
import struct
import ntplib
from datetime import datetime
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
		start = time.time()
		response = client.request(ntpserver, port=ntpport, version=ntpversion)
		ctrlPipe.send(f"{NTPOFFSET}{response.offset}")
		time.sleep((1 / ntpFrequency) - (time.time() - start))


def tcpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((receiver, tcpport))
	s.connect((sender, tcpport))
	while True:
		if ctrlPipe.poll():
			msg = ctrlPipe.recv()
			if (False):
				pass
			else:
				print(msg)
				print("Encountered unexpected message in receiver TCP pipe.")
		else:
			# Poll the socket for messages
			s.setblocking(False)
			try:
				recv = s.recv(4096)
				if (len(recv) > 0):
					print(f"Received message on TCP channel: {recv}")
			except socket.timeout as e:
				if e.args[0] != 'timed out':
					print(f"Encountered unexpected error in tcp fn: {e}")
			s.setblocking(True)
		# If neither pipe nor socket has messages, yield thread
		time.sleep(0.005)

def udpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setblocking(False)
	s.bind((receiver, udpport))
	carryover = None
	while True:
		timeOffset = 0
		try:
			# Check for control message
			if ctrlPipe.poll():
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
			# Mark in case last segment is dropped
			if carryover is None:
				# Try to receive, will throw socket.timeout if no content
				content = s.recv(1500)
			else:
				content = carryover
				carryover = None
			frameid, index = struct.unpack('>II', content[:8])
			if index != 0:
				print(f"First index received != 0. For frame {frameid}, we dropped packets 0 (inclusive) to {index} (exclusive).")
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
							print(f"Received partial frame for frameid = {frameid}, segments {previous} -> {index}, exclusive")
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
			ctrlPipe.send(FRAMERECEIVED + framesize.to_bytes(4, byteorder='big') + struct.pack('>d', getTime(timeOffset)))
			# Then go back to non-blocking
			s.setblocking(False)
		except KeyboardInterrupt as e:
			# Handle ctrlC
			s.close()
			ctrlPipe.send(EXITSTRING)
			ctrlPipe.close()
		except socket.timeout as e:
			# Handle socket time outs
			print(f"Received error2: {e}")
			ermsg = e.args[0]
			if ermsg == 'timed out':
				time.sleep(0.01)
				continue
		except socket.error as e:
			# Handle other errors, like no-data on socket recv when socket in non-block mode
			if len(e.args) > 0:
				if e.args[0] == 11:
					time.sleep(0.01)
					continue 
			else:
				s.close()
				ctrlPipe.send(EXITSTRING)
				ctrlPipe.close()

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
		udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe,))
		tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe,))
		ntpProcess = mp.Process(name=ntpName, target=ntpFn, args=(ntpFnPipe,))

		# Process comms: 
		# 		NTP client reports time offset to main process, main process forwards to TCP and UDP. 
		# 		Main thread and UDP only exchange exit messages.
		# 							
		# Process communication: main thread <--EXITONLY--> NTP server
		# 											 main thread <--EXITONLY--> UDP 
		# 											 UDP --> TCP (UDP will forward exit message to TCP when received ==> UDP server can't return exit until TCP has successfully exited)
		
		processes = [(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe), (ntpProcess, ntpMainPipe)]
		# Start them
		udpProcess.start()
		tcpProcess.start()
		ntpProcess.start()
		# Wait until program is over
		pipes = [x for _, x in processes]
		while True:
			readyPipes = mp.connection.wait(pipes)
			for pipe in readyPipes:
				rc = pipe.recv()
				if rc[:len(NTPOFFSET)] == NTPOFFSET:
					udpMainPipe.send(rc)
					tcpMainPipe.send(rc)
				elif rc[:len(EXITSTRING)] == EXITSTRING:
					if pipe != tcpMainPipe:
						tcpMainPipe.send(EXITSTRING)
					if pipe != udpMainPipe:
						udpMainPipe.send(EXITSTRING)
					if pipe != ntpMainPipe:
						ntpMainPipe.send(EXITSTRING)
					break
				else:
					print(f"Unhandled pipe message: {pipe.recv()}")
	except KeyboardInterrupt:
		# Every process/subprocess receives kb interrupt
		# So we don't manually need to do anything here -they'll finish on their own
		pass
	print("Received keyboard interrupt - now join()ing all processes...")
	for process, _ in processes:
		process.join()
	print("Successfully joined all processes. Exiting...")
	exit (0)


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
