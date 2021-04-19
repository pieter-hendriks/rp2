import os
import socket
import time
from values import *
import multiprocessing as mp

def ntpFn():
	pass

def tcpFn(ctrlPipe: mp.Pipe):
	pass

def udpFn(ctrlPipe: mp.Pipe):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setblocking(False)
	s.bind((receiver, udpport))
	while True:
		try:
			# Check for control message
			if ctrlPipe.poll():
				msg = ctrlPipe.recv()
				# Handle exit
				if msg == 'exit':
					s.close()
					ctrlPipe.send(exitString)
					ctrlPipe.close()
					break
			# Try to receive, will throw socket.timeout if no content
			content = s.recv(8192)
			# When we've received anything, block for a bit to receive all parts of the message
			s.setblocking(True)
			s.settimeout(0.3)
			try:
				while (len(content) < framesize):
					content += s.recv(8192)
			except socket.timeout as e:
					# Report error if we encounter one (Packet dropped)
					ctrlPipe.send(PARTIALFRAME)
				
			# Report error, incorrect frame size received
			if len(content) != framesize:
				ctrlPipe.send(WRONGFRAMESIZE)
			# Record frame reception time
			ctrlPipe.send(FRAMERECEIVED + framesize.to_bytes(4, byteorder='big') + struct.pack('>d', time.time()))
			# Then go back to non-blocking
			s.setblocking(False)
		except KeyboardInterrupt as e:
			# Handle ctrlC
			s.close()
			ctrlPipe.send(exitString)
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
				ctrlPipe.send(exitString)
				ctrlPipe.close()



def main():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((receiver, udpport))
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
			soc.sendto(ackmsg, addr)
			# Add frame to received total size
			total += len(frame)
		# Record end time and output data
		end = time.time()
		print(f"Received {total} bytes of data, over {loopLength} frames.\nThis occured over {float(int(10 * (end - start)) / 10)} seconds (goal time was {float(int(10 * (loopLength/framerate)) / 10)} seconds).")
	finally:
		s.close()

if __name__ == "__main__":
	try:
		# Basic setup of variables
		processes = []
		udpName = 'UDP receiver'
		#tcpName = 'TCP reporting'

		# Construct pipes for interprocess communication
		udpFnPipe, udpMainPipe = mp.Pipe()
		#tcpFnPipe, tcpMainPipe = mp.Pipe()


		# Create the processes
		udpProcess = mp.Process(name=udpName, target=udpFn, args=(udpFnPipe,))
		#tcpProcess = mp.Process(name=tcpName, target=tcpFn, args=(tcpFnPipe,))

		# Close our copy of the Fn pipes
		#udpFnPipe.close()
		#tcpFnPipe.close()

		# Process communication: main thread <--EXITONLY--> NTP server
		# 											 main thread <--EXITONLY--> UDP 
		# 											 UDP --> TCP (UDP will forward exit message to TCP when received ==> UDP server can't return exit until TCP has successfully exited)
		
		processes = [(udpProcess, udpMainPipe)] #[(udpProcess, udpMainPipe), (tcpProcess, tcpMainPipe)]
		# Start them
		udpProcess.start()
		#tcpProcess.start()
		# Wait until program is over
		pipes = [x for _, x in processes]
		while True:
			readyPipes = mp.connection.wait(pipes)
			for pipe in readyPipes:
					print(f"Unhandled pipe message: {pipe.recv()}")
	except KeyboardInterrupt:
		# Main process, and all subprocesses, receive the KeyboardInterrupt
		# So all we have to do is wait for them to finish.
		i = 0
		for process, pipe in processes:
			# Child processes also receive SigInt, so we don't have to manually send anything here.
			msg = pipe.recv()
			# Mention output if unexpected
			if msg != exitString:
				print(f"Bad output at KeyboardInterrupt (process index = {i}): {msg}")
			else:
				print(f"{msg} received from ntp server, expected value.")
			# Increment function index, so output will remain correct for all functions
			i = i+1
			# We're exiting, so close the pipe. We expect no further communication as both processes will end.
			pipe.close()
			# Join the process, ensuring we can gracefully exit when this script terminates.
			process.join()
