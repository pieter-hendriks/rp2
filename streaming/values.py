import os

ackmsg = b'ack'
ackLength = len(ackmsg)
framerate = 80; frametime = 1/framerate
datarate = 5e7
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)
frameSegmentSize  = 1280
frameSegments = [frame[i*frameSegmentSize: (i+1)*frameSegmentSize] for i in range(int(framesize/frameSegmentSize) + 1)]

sender = '192.168.4.2'
receiver = '192.168.3.2'

ntpserver = '192.168.1.26'#sender
ntpclient= '192.168.1.8'#receiver
udpport = 50000
tcpport = 50001
ntpport = 50123

loopLength = 5
ntpversion = 3
ntpFrequency = 1 # Number of times per second to send ntp request

EXITSTRING = b'EXIT'

UDPSENDTIME = b'UST'
TCPFRAMEREPORT = b'TFR'
TCPRESCALE = b'TRS'
PARTIALFRAME = b'URP'
WRONGFRAMESIZE = b'UBF'
FRAMERECEIVED = b'URF'
NTPOFFSET = b'NOS'
