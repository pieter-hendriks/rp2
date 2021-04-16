import os


framerate = 80; frametime = 1/framerate
datarate = 300000
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)
ackLength = 3


sender = '192.168.4.2'
receiver = '192.168.3.2'
port = 50000

loopLength = 160
