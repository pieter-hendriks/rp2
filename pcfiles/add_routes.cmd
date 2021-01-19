route ADD 192.168.200.0 MASK 255.255.255.0 192.168.100.2 IF 6
route ADD 192.168.100.0 MASK 255.255.255.0 192.168.200.2 IF 17
route ADD 192.168.200.0 MASK 255.255.255.0 192.168.200.2 IF 17
route ADD 192.168.100.0 MASK 255.255.255.0 192.168.100.2 IF 6
REM  18...2c f0 5d 8a d3 58 ......Realtek PCIe 2.5GbE Family Controller 192.168.1.8
REM  17...2c f0 5d 8a d3 59 ......Realtek PCIe GbE Family Controller 192.168.200.5
REM  10...0a 00 27 00 00 0a ......VirtualBox Host-Only Ethernet Adapter
REM  6...d0 37 45 1e ce 03 ......TP-LINK Gigabit Ethernet USB Adapter 192.168.100.5
REM  12...5c f3 70 a0 1f 70 ......Bluetooth Device (Personal Area Network)
REM  1...........................Software Loopback Interface 1
REM  42...00 15 5d 17 b2 63 ......Hyper-V Virtual Ethernet Adapter

REM => 17 & 6 currently