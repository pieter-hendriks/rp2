ROBOT=192.168.85.159


launchRobotStuff() {
  echo "Issuing remote command!"
  sshpass -p "rover" ssh rover@${ROBOT} "./startRobot.sh"
  echo "Remote ending..."
}

launchLocalStuff() {
  echo "Issuing local commands"
  cd ~/school/rp2/streaming
  source ~/school/rp2/venv/bin/activate
  python ~/school/rp2/streaming/sender.py
  deactivate
  echo "Local ending..."
}

launchRobotStuff &
# Local stuff is sender; sender waits for trigger frame from receiver to start moving
# Receiver is started after  ros; roughly 4.5 seconds to give ros initialization time to go.
launchLocalStuff &

wait $!
echo "Local is finished. "
#echo "Sleeping for up to 10 seconds, allowing remote to handle frame writing."
#sleep 10
#echo "Killing remote!"
#sshpass -p "rover" ssh rover@${ROBOT} "source killRobot.sh"
echo "Waiting for remote to finish..."
echo "If this takes too long, please check remote to see if anything has gone wrong."
echo "/home/rover/killRobot.sh script can fix this, probably."
wait
