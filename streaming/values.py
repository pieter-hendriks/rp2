import os

ackmsg = b'ack'
ackLength = len(ackmsg)
framerate = 80; frametime = 1/framerate
datarate = 7e7
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)
messageSize  = 1280  # Should fit within ~1500 MTU
frameSegments = [frame[i*messageSize: (i+1)*messageSize] for i in range(framesize/messageSize + 1)]

sender = '192.168.4.2'
receiver = '192.168.3.2'
udpport = 50000
tcpport = 50001
ntpport = 50123

loopLength = 5


exitString = 'EXIT'

UDPSENDTIME = 'UST'
TCPFRAMEREPORT = 'TFR'
PARTIALFRAME = 'URP'
WRONGFRAMESIZE = 'UBF'
FRAMERECEIVED = 'URF'