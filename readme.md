> Uses script in ready folder to be installed to Raspi 3

> Settings in Raspi 3
- To make faster in booting
	1. Setting in "/etc/network/interfaces" to like this :
	   "allow-hotplug eth0"
	   "iface eth0 inet dhcp"
	2. Set timeout to 15 in file "/etc/dhcp/dhclient.conf"
	   "timeout=15;"
	3. In "raspi-config" select "no" in waiting to connect to network in booting