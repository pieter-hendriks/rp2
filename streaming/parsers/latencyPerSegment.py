import os
#abspath = os.path.abspath(__file__)
#dname = os.path.dirname(abspath)
#os.chdir(dname)
import findLatestLogfolder
import matplotlib.pyplot as plt
getLatestLogFolder = findLatestLogfolder.getLatestLogFolder
latest_send = os.path.join(getLatestLogFolder('send_log_').path, 'segment_send.log')
latest_recv = os.path.join(getLatestLogFolder('recv_log_').path, 'segment_arrivals.log')
with open(latest_send, 'r') as f:
    send = [eval(x) for x in f.readlines()]
with open(latest_recv, 'r') as f:
    recv = [eval(x) for x in f.readlines()]

recvTimes = {(recv[i][0], recv[i][1]): recv[i][2] for i in range(len(recv))}
sendTimes = {(send[i][0], send[i][1]): send[i][2] for i in range(len(send))}

latencies = []
for key in recvTimes:
    if (recvTimes[key] < sendTimes[key]):
        print("Excuse me but what the fuck.")
        print(recvTimes[key])
        print(sendTimes[key])
        print(recvTimes[key] - sendTimes[key])
        print(key)
        print("Wtf2.0endmark")
        raise 1
    latencies.append(recvTimes[key] - sendTimes[key])
plt.plot(range(len(latencies)), latencies)
plt.show()
