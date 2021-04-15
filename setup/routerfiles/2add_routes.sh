# Add routes for the client router
# Assumes IP 192.168.2.1 for 60G AP, 192.168.2.2 for 60G client
# LAN interface 192.168.100.2 on AP side, 192.168.200.2 on client side
# Computer interfaces 192.168.100.5 connected to AP, 192.168.200.5 connected to client (both wired)
ip route add 192.168.100.0/24 via 192.168.2.1 dev wlan2