import ntplib
import time
client = ntplib.NTPClient()
for _ in range(100):
	response = client.request('192.168.1.8', port='50123', version=3)
	print(f"{response.offset}")
	time.sleep(0.5)