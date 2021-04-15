#!/bin/bash

DEV_USB="enxd037451ece03"
DEV_NAT="enp6s0"


# Configure IP addresses for our local interfaces
# 1 -> 3 is a cable, 2 -> 4 is a cable
sudo ip addr add 192.168.4.2/24 dev ${DEV_USB}
sudo ip addr add 192.168.3.2/24 dev ${DEV_NAT}

# Add the routes 
# Direct route pc -> router
	# 200.1 is reachable from USB (200.3)
	# 200.2 is reachable from NAT (200.4)
# Routes between interfaces: 
	# 200.4 from 200.3 through 200.1 (DEV_USB)
	# 200.3 from 200.4 through 200.2 (DEV_NAT)

# We assume router are configured correctly for this.
# ie -> incoming 200.4 on 200.2 is routed through wireless (2.2) to (2.1) and from there (2.1) forwards through 200.1 to 200.4
sudo ip route add 192.168.4.1 dev ${DEV_USB} metric 100
sudo ip route add 192.168.2.1 via 192.168.4.1 dev ${DEV_USB} metric 100
sudo ip route add 192.168.3.1 via 192.168.4.1 dev ${DEV_USB} metric 100
sudo ip route add 192.168.3.1 dev ${DEV_NAT} metric 100
sudo ip route add 192.168.2.2 via 192.168.3.1 dev ${DEV_NAT} metric 100
sudo ip route add 192.168.4.1 via 192.168.3.1 dev ${DEV_NAT} metric 100

