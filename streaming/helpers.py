from values import *
import multiprocessing as mp


def handleSenderInterprocessCommunication(receivedMessage, udpPipe: mp.Pipe,
                                          tcpPipe: mp.Pipe, ntpPipe: mp.Pipe):
	# Handle interprocess pipe communication
	# There's probably a more elegant way to implement this. Oh well.
	if receivedMessage[:len(NTPOFFSET)] == NTPOFFSET:
		print("Sending received NTP offset to UDP and TCP!")
		udpPipe.send(receivedMessage)
		tcpPipe.send(receivedMessage)
	elif receivedMessage[:len(EXITSTRING)] == EXITSTRING:
		print("Sending EXIT everywhere!")
		#if receivedPipe != tcpPipe:
		tcpPipe.send(EXITSTRING)
		#if receivedPipe != udpPipe:
		udpPipe.send(EXITSTRING)
		#if receivedPipe != ntpPipe:
		ntpPipe.send(EXITSTRING)
	elif receivedMessage[:len(UDPSENDTIME)] == UDPSENDTIME:
		print("implement UDPSENDTIME handling pls")
	elif receivedMessage[:len(TCPFRAMEREPORT)] == TCPFRAMEREPORT:
		print("implement TCPFRAMEREPORT handling pls")
	elif receivedMessage[:len(TCPRESCALE)] == TCPRESCALE:
		print("implement TCPRESCALE handling pls")
	elif receivedMessage[:len(WRONGFRAMESIZE)] == WRONGFRAMESIZE:
		print("implement WRONGFRAMESIZE handling pls")
	elif receivedMessage[:len(PARTIALFRAME)] == PARTIALFRAME:
		print("implement PARTIALFRAME handling pls")
	elif receivedMessage[:len(FRAMERECEIVED)] == FRAMERECEIVED:
		print("implement FRAMERECEIVED handling pls")
	elif receivedMessage[:len(NTPOFFSET)] == NTPOFFSET:
		print("implement NTPOFFSET handling pls")
	else:
		print(f"Unhandled pipe message: {receivedMessage}")


def handleReceiverInterprocessCommunication(receivedMessage, udpPipe, tcpPipe,
                                            ntpPipe):
	# Handle interprocess pipe communication
	# There's probably a more elegant way to implement this. Oh well.
	if receivedMessage[:len(NTPOFFSET)] == NTPOFFSET:
		udpPipe.send(receivedMessage)
		tcpPipe.send(receivedMessage)
	elif receivedMessage[:len(EXITSTRING)] == EXITSTRING:
		#if pipe != tcpPipe:
		tcpPipe.send(EXITSTRING)
		#if pipe != udpPipe:
		udpPipe.send(EXITSTRING)
		#if pipe != ntpPipe:
		ntpPipe.send(EXITSTRING)
	elif receivedMessage[:len(UDPSENDTIME)] == UDPSENDTIME:
		print("implement UDPSENDTIME handling pls")
	elif receivedMessage[:len(TCPFRAMEREPORT)] == TCPFRAMEREPORT:
		print("implement TCPFRAMEREPORT handling pls")
	elif receivedMessage[:len(TCPRESCALE)] == TCPRESCALE:
		print("implement TCPRESCALE handling pls")
	elif receivedMessage[:len(WRONGFRAMESIZE)] == WRONGFRAMESIZE:
		print("implement WRONGFRAMESIZE handling pls")
	elif receivedMessage[:len(PARTIALFRAME)] == PARTIALFRAME:
		print("implement PARTIALFRAME handling pls")
	elif receivedMessage[:len(FRAMERECEIVED)] == FRAMERECEIVED:
		print("implement FRAMERECEIVED handling pls")
	elif receivedMessage[:len(NTPOFFSET)] == NTPOFFSET:
		print("implement NTPOFFSET handling pls")
	else:
		print(f"Unhandled pipe message: {receivedMessage}")
