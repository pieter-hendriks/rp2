from icmplib import ICMPv4Socket, ICMPRequest, ICMPReply
import ctypes, sys, os
import time
from matplotlib import pyplot as plt
import threading
import concurrent.futures


destination = '192.168.2.2'
source = '192.168.3.2'
def now_us():
	# Return current time stamp in microseconds
	tics = ctypes.c_int64()
	freq = ctypes.c_int64()

	#get ticks on the internal ~2MHz QPC clock
	ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
	#get the actual freq. of the internal ~2MHz QPC clock
	ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))  

	t_us = tics.value*1e6/freq.value
	return t_us
	
def sender(socket, count, sleeptime_us = 5000):
	sendTimes = []
	for i in range(count):
		req = ICMPRequest(destination, 0, i)
		socket.send(req)
		sendTimes.append(req.time)
		before = now_us()
		while (before + sleeptime_us > now_us()):
			time.sleep(0)
		after = now_us()
		print((after - before)/1000000.0)
	return sendTimes

def receiver(socket, count):
	recvTimes = []
	for _ in range(count):
		recv = socket.receive()
		recvTimes.append(recv.time)
	return recvTimes
		
def threaded_main():
	socket = ICMPv4Socket(source)
	count = 1000
	with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
		recvFuture = executor.submit(receiver, socket, count)
		sendFuture = executor.submit(sender, socket, count)
	#receiver = threading.Thread(target=receiver, args=(socket, 100))
	#sender = threading.Thread(target=sender, args=(socket, 100))
	#receiver.start()
	#sender.start()
	#sender.join()
	#receiver.join()
	recvTimes = sendFuture.result()
	sendTimes = recvFuture.result()
	latencies = [(x, y) for x,y in zip(sendTimes, recvTimes)]
	print(latencies)
	plt.plot([x[0] - x[1] for x in latencies])
	plt.show()
	

def main():
	socket = ICMPv4Socket(source)
	latencies = []
	for i in range(100):
		req = ICMPRequest(destination, 0, i)
		socket.send(req)
		recv = socket.receive(req)
		rtt = recv.time - req.time
		#if (rtt < 0.01):
		#	time.sleep(0.01 - rtt)
		latencies.append((recv.time, req.time))
	print(latencies)
	plt.xlabel("Ping index")
	plt.ylabel("RTT (ms)")
	plt.plot([int((x[0] - x[1]) * 1000 + 0.5) for x in latencies])
	plt.show()
	
def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
	if isAdmin():
		threaded_main()
	else:
		ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
		
