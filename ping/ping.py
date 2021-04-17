from icmplib import ICMPv4Socket, ICMPRequest, ICMPReply, TimeoutExceeded
import ctypes, sys, os
import time
from matplotlib import pyplot as plt
import threading
import concurrent.futures


destination = '192.168.2.2'
source = '192.168.3.2'
def sender(socket, count, sleeptime = 0):
	sendTimes = []
	for i in range(count):
		#print(f"Sending {i}")
		req = ICMPRequest(destination, 12354, i)
		socket.send(req)
		sendTimes.append(req.time)
		before = time.time() 
		while (before + sleeptime > time.time()):
			time.sleep(0)
		after = time.time()
	return sendTimes

def receiver(socket, count):
	recvTimes = []
	for i in range(count):
		recv = None
		while not recv or recv.id != 12354:
			try:
				recv = socket.receive()
				add = 0
				while recv.bytes_received + add < 64: 
					recv2 = socket.receive()
					add = recv2.bytes_received
					recv = recv2
				recvTimes.append(recv.time)
			except TimeoutExceeded:
				recvTimes.append(None)
		#print(f"Received {i}")
	return recvTimes
		
def main():
	start = time.time()
	socket = ICMPv4Socket(source)
	count = 10000
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
	count = len(latencies)
	print(latencies)
	latencies = [(x, y) for x,y in latencies if x is not None and y is not None]
	dropped = count - len(latencies)
	plt.plot([x[0] - x[1] for x in latencies])
	stop = time.time()
	print (f"Total program runtime was {stop - start:.2f} seconds.")
	print (f"{dropped} packets out of {count} were dropped (and thus not graphed).")
	plt.show()
	


def isAdmin():
	if os.name=='nt':
		try:
				return ctypes.windll.shell32.IsUserAnAdmin()
		except:
				return False
	elif os.name=='posix':
		try:
			return os.geteuid() == 0
		except:
			return False

	else:
		print("Unsure how to handle admin check on this OS.")
		raise OSError("WOOPSIES")

if __name__ == "__main__":
	if not isAdmin():
		if os.name == 'nt':
			print("Not admin. Re-running as admin...")
			ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
			exit(0)
		elif os.name == 'posix':
			print("Not sudo - re-running as sudo...")
			args = ['sudo', sys.executable] + sys.argv + [os.environ]
			os.execlpe('sudo', *args)
			print(f"Current euid: {os.geteuid()}")
	main()
			
		
