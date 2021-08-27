#!/bin/bash
cd "$(dirname "$0")"
rm -r streaming/log/*
sshpass -p "rover" ssh rover@10.1.75.85 "rm -r /home/rover/pieter/streaming/log/*"
