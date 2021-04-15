import ctypes
import os
CLOCK_MONOTONIC_RAW = 4
class timespec(ctypes.Structure):
	_fields_= [
		('tv_sec', ctypes.c_long), 
		('tv_nsec', ctypes.c_long)
	]
# Configure Python access to clock_gettime from C library
librt = ctypes.CDLL('librt.so.1', use_errno=True)
clock_gettime = librt.clock_gettime
# Specify input arguments
clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

def now_s():
	# Current time in seconds
	t = timespec()
	if clock_gettime(CLOCK_MONOTONIC_RAW, ctypes.pointer(t)) != 0:
		errno_ = ctypes.get_errno()
		raise OSError(errno_, os.strerror(errno_))
	return t.tv_sec + t.tv_nsec * 1e-9

def now_us():
	# Current time in microseconds
	return now_s()*1e6 #  Seconds function returns a float, multiply to correct unit
def now_ms():
	# Current time in milliseconds
	return now_s()*1e3 #  Seconds function returns a float, multiply to correct unit