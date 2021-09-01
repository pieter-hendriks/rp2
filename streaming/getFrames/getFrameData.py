import cv2
import os
import time

output_directory = 'frames'
input_file = 'Drive.mp4'

try:
	os.mkdir(output_directory)
except OSError:
	print("Failed to create the output directory.")
	exit(1)
start = time.time()
cap = cv2.VideoCapture(input_file)
framecount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
i = 0
while cap.isOpened():
	ret, frame = cap.read()
	if not ret:
		print("Failed to read frame.")
		exit(1)
	cv2.imwrite(f'{output_directory}/frame_{i}.jpg', frame)
	i += 1
	if (i == framecount):
		end = time.time()
		cap.release()
		break
print("Successfully extracted all images from the video file.")
print(f"Process completed in {time.time() - start:.3f} seconds.")
