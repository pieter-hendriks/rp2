#!/bin/bash

sudo ip addr add 192.168.3.2/24 dev enp6s0
sudo route add -net 192.168.2.0/24 gw 192.168.3.1
sudo route add -net 192.168.4.0/24 gw 192.168.3.1
