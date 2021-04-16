# https://stackoverflow.com/questions/38319606/how-can-i-get-millisecond-and-microsecond-resolution-timestamps-in-python
# Current implementation only has UNIX version. 
# ping.py has windows code, from same answer
# Probably worth merging both into this file.
# TODO

import ctypes
import os
if os.name == 'nt':
	def _getTicksAndFrequency():
		tics = ctypes.c_int64()
		freq = ctypes.c_int64()

		ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics))
		ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
		return tics, freq
	def now_us():
		tics, freq = _getTicksAndFrequency()
		return tics.value * 1e6 / freq.value
	def now_ms():
		tics, freq = _getTicksAndFrequency()
		return tics.value * 1e3 / freq.value
	def now_s():
		tics, freq = _getTicksAndFrequency()
		return tics.value / freq.value

elif os.name == 'posix':
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

import time
def wait_ms(t):
	start = now_ms()
	while (now_ms() - start < t):
		time.sleep(0) # Should be essentially no time at all, but does allow other things to be scheduled. Should be slightly better than full-on busy waiting.
	return
def wait_s(t):
	start = now_s()
	while (now_s() - start < t):
		time.sleep(0) # Should be essentially no time at all, but does allow other things to be scheduled. Should be slightly better than full-on busy waiting.
	return

def wait_us(t):
	start = now_us()
	while (now_us() - start < t):
		time.sleep(0) # Should be essentially no time at all, but does allow other things to be scheduled. Should be slightly better than full-on busy waiting.
	return