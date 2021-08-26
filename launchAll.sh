launchRobotStuff() {
  echo "Issuing remote command!"
  sshpass -p "rover" ssh rover@10.1.75.85 "source startRobot.sh"
  echo "Remote ending..."
}

launchLocalStuff() {
  echo "Issuing local commands"
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
echo "Local is finished. Killing remote in 5 seconds..."
sleep 5
echo "Killing remote!"
sshpass -p "rover" ssh rover@10.1.75.85 "source killRobot.sh"
wait
