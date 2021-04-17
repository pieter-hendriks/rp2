import os

ackmsg = b'ack'
ackLength = len(ackmsg)
framerate = 80; frametime = 1/framerate
datarate = 7e7
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)

sender = '192.168.4.2'
receiver = '192.168.3.2'
port = 50000

loopLength = 1600
