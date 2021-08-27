#!/bin/bash
rm -r streaming/log/*
sshpass -p "rover" ssh rover@10.1.75.85 "rm -r /home/rover/pieter/streaming/log/*"
