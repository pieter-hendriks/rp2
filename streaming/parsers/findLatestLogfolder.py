import os
import datetime
def getLatestLogFolder(to_match, basePath='/home/pieter/school/rp2/streaming/log'):
    # From folder contents, filter on directories and file names containing the keyword
    directories = [x for x in os.scandir(basePath) if x.is_dir() and to_match in x.name]
    # These directories are created with a specific format, we abuse that 
    # to filter fairly quickly. Any changes to naming scheme will break this.
    # Specifically, they're named recv_img_{}, recv_log_{} and send_log_{}
    # Meaning we can just skip the first 9 characters and get what we want
    latest = None
    for directory in directories:
        # Short circuit first loop, has no logic
        if latest is None:
            latest = directory
            continue
        latestTime = datetime.datetime.fromisoformat(latest.name[9:])
        dirTime = datetime.datetime.fromisoformat(directory.name[9:])
        if dirTime > latestTime:
            latest = directory
    return latest




if __name__ == '__main__':
    print(getLatestLogFolder('recv_log'))
