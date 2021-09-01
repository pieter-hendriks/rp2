ROBOT="192.168.4.2"
mkdir -p "/home/pieter/school/rp2/results/moving/$1"
mkdir -p "/home/pieter/school/rp2/results/static/$1"
sshpass -p "rover" scp -r "rover@${ROBOT}:/home/rover/pieter/streaming/log/*" "/home/pieter/school/rp2/results/moving/$1"
sshpass -p "rover" ssh "rover@${ROBOT}" "rm -r /home/rover/pieter/streaming/log/*"
cp -r /home/pieter/school/rp2/streaming/log/* "/home/pieter/school/rp2/results/static/$1"
rm -r /home/pieter/school/rp2/streaming/log/*
