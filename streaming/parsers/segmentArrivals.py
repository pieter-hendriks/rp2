if __name__ == "__main__":
    path = input("Please enter full path to file:\n")
    #path = "/home/pieter/school/rp2/streaming/log/recv_log_2021-08-28T12:08:55.196719/segment_arrivals.log"
    entries = []
    with open(path, 'r') as f:
        entries = [eval(x) for x in f.readlines()]
    badTimes = [i for i in range(1, len(entries)) if entries[i][2] < entries[i-1][2]]
    test = [badTimes[i] - badTimes[i-1] for i in range(1, len(badTimes))]
    print(badTimes)
    print(test)
    print(len(badTimes))
    print(len(entries))
