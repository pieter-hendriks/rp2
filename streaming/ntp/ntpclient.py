import ntplib
import time
from datetime import datetime
ntpport = 50123

client = ntplib.NTPClient()
offset = 0
for _ in range(100):
	response = client.request('192.168.1.26', port=ntpport, version=3)
	print(response.offset)
	time.sleep(0.3)
