import os
framerate = 80; frametime = 1/framerate
datarate = 300000
framesize = int(datarate / framerate + 0.5)
# Use random data as frame
# Can simply use same frame every time - no need to re-generate each iteration
frame = os.urandom(framesize)