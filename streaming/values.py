import os

ackmsg = b'ack'
ackLength = len(ackmsg)
framerate = 80; frametime = 1/framerate
datarate = 5e7
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)
frameSegmentSize  = 1280  # Should fit within ~1500 MTU
frameSegments = [frame[i*frameSegmentSize: (i+1)*frameSegmentSize] for i in range(int(framesize/frameSegmentSize) + 1)]

sender = '192.168.4.2'
receiver = '192.168.3.2'
udpport = 50000
tcpport = 50001
ntpport = 50123

loopLength = 5


exitString = b'EXIT'

UDPSENDTIME = b'UST'
TCPFRAMEREPORT = b'TFR'
PARTIALFRAME = b'URP'
WRONGFRAMESIZE = b'UBF'
FRAMERECEIVED = b'URF'