#!/bin/bash
ROBOT=192.168.85.159
cd "$(dirname "$0")"
rm -r streaming/log/*
sshpass -p "rover" ssh rover@${ROBOT} "rm -r /home/rover/pieter/streaming/log/*"
