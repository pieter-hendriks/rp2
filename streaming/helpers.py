from values import config
import multiprocessing as mp
import struct

def handleSenderInterprocessCommunication(receivedMessage, udpPipe: mp.Pipe, tcpPipe: mp.Pipe, ntpPipe: mp.Pipe):
	# Handle interprocess pipe communication
	# There's probably a more elegant way to implement this. Oh well.
	if receivedMessage[:len(config.NTPOFFSET)] == config.NTPOFFSET:
		print("Sending received NTP offset to UDP and TCP!")
		udpPipe.send(receivedMessage)
		tcpPipe.send(receivedMessage)
	elif receivedMessage[:len(config.EXITSTRING)] == config.EXITSTRING:
		print("Sending EXIT everywhere!")
		#if receivedPipe != tcpPipe:
		tcpPipe.send(config.EXITSTRING)
		#if receivedPipe != udpPipe:
		udpPipe.send(config.EXITSTRING)
		#if receivedPipe != ntpPipe:
		ntpPipe.send(config.EXITSTRING)
	elif receivedMessage[:len(config.UDPSENDTIME)] == config.UDPSENDTIME:
		# These are sent with two doubles, the time we start sending and time we stop sending.
		# Send occurs in between these two values.
		sendStart, sendEnd = struct.unpack('>dd', receivedMessage[len(config.UDPSENDTIME):])
		openMode = 'w' if config.isFirstFrame() else 'a'
		with open(config.getLogFileName("sendStartTimes"), openMode) as f:
			f.write(f"{sendStart}, ")
		with open(config.getLogFileName("sendEndTimes"), openMode) as f:
			f.write(f"{sendEnd}, ")
		config.markFrameDone()
	elif receivedMessage[:len(config.TCPFRAMEREPORT)] == config.TCPFRAMEREPORT:
		print("implement TCPFRAMEREPORT handling pls")
	elif receivedMessage[:len(config.TCPRESCALE)] == config.TCPRESCALE:
		print("implement TCPRESCALE handling pls")
	elif receivedMessage[:len(config.WRONGFRAMESIZE)] == config.WRONGFRAMESIZE:
		print("implement WRONGFRAMESIZE handling pls")
	elif receivedMessage[:len(config.PARTIALFRAME)] == config.PARTIALFRAME:
		print("implement PARTIALFRAME handling pls")
	elif receivedMessage[:len(config.FRAMERECEIVED)] == config.FRAMERECEIVED:
		print("implement FRAMERECEIVED handling pls")
	elif receivedMessage[:len(config.NTPOFFSET)] == config.NTPOFFSET:
		print("implement NTPOFFSET handling pls")
	else:
		print(f"Unhandled pipe message: {receivedMessage}")


def handleReceiverInterprocessCommunication(receivedMessage, udpPipe: mp.Pipe, tcpPipe: mp.Pipe, ntpPipe: mp.Pipe):
	# Handle interprocess pipe communication
	# There's probably a more elegant way to implement this. Oh well.
	if receivedMessage[:len(config.NTPOFFSET)] == config.NTPOFFSET:
		udpPipe.send(receivedMessage)
		tcpPipe.send(receivedMessage)
	elif receivedMessage[:len(config.EXITSTRING)] == config.EXITSTRING:
		#if pipe != tcpPipe:
		tcpPipe.send(config.EXITSTRING)
		#if pipe != udpPipe:
		udpPipe.send(config.EXITSTRING)
		#if pipe != ntpPipe:
		ntpPipe.send(config.EXITSTRING)
	elif receivedMessage[:len(config.UDPSENDTIME)] == config.UDPSENDTIME:
		print("implement UDPSENDTIME handling pls")
	elif receivedMessage[:len(config.TCPFRAMEREPORT)] == config.TCPFRAMEREPORT:
		print("implement TCPFRAMEREPORT handling pls")
	elif receivedMessage[:len(config.TCPRESCALE)] == config.TCPRESCALE:
		print("implement TCPRESCALE handling pls")
	elif receivedMessage[:len(config.WRONGFRAMESIZE)] == config.WRONGFRAMESIZE:
		print("implement WRONGFRAMESIZE handling pls")
	elif receivedMessage[:len(config.PARTIALFRAME)] == config.PARTIALFRAME:
		print("implement PARTIALFRAME handling pls")
	elif receivedMessage[:len(config.FRAMERECEIVED)] == config.FRAMERECEIVED:
		print("implement FRAMERECEIVED handling pls")
	elif receivedMessage[:len(config.NTPOFFSET)] == config.NTPOFFSET:
		print("implement NTPOFFSET handling pls")
	else:
		print(f"Unhandled pipe message: {receivedMessage}")
