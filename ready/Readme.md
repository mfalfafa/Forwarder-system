## Settings ##
### Forwarder settings : ###
1. install **Raspbian Jessie Lite**
2. **sudo raspi-config**
	- **Network options**
		- in **Wi-fi**, enter **SSID** and **Password**
	- **boot options**
		- in **Desktop/CLI**, select **Console autologin**
		- in **Wait for network**, select **No** in **Wait until a network connection is established**
		- in **Splash screen**, select **No** in showing splash screen
	- **interfacing options**
		- in **SSH**, select **yes** to enable SSH
	- Update Raspi 3 in **Update** menu
	- **Reboot** Raspi
3. Edit file **/etc/dhcpcd.conf** to make static IP for **eth0** interface
	```
	interface eth0
	static ip_address=192.168.10.xx/24	//xx : based on client configuration
	static routers=192.168.10.1
	```
4. Edit file **/etc/dhcp/dhclient.conf** to give timeout in booting time
	```
	uncomment timeout option and change the value :
	timeout=15;
	```
5. Install **git** in Raspi 3
	```
	sudo apt-get install git
	```
6. Install python 3 modules
	```
	sudo pip3 install RPi.GPIO
	sudo pip3 install pyserial
	```
7. Clone Forwarder files from github in **home/pi/**
	```
	git clone https://github.com/mfalfafa/Forwarder-system.git
	or
	git clone git://github.com/mfalfafa/Forwarder-system.git
	```
8. Edit file **/etc/profile** and add the following command
	```
	sudo python3 /home/pi/Forwarder-system/ready/Forwarder-v1_x.py
	x : based on client configuration
	```
9. Test that all settings are work by reboot
	```
	sudo reboot now
	```
10. If all settings are working (no error), disable **wlan0** to prevent IP conflict between **eth0** and **wlan0**. In file **/boot/config.txt** add the following command
	```
	dtoverlay=pi3-disable-wifi
	```
	So if you want to use SSH, then you must connect to Raspi 3 with LAN Port
---
### DataCollector settings : ###
1. Same as Forwarder
2. Same as Forwarder
3. Same as Forwarder (based on DataCollector configuration)
4. Same as Forwarder
5. Same as Forwarder
6. Install python 3 modules
	```
	sudo pip3 install RPi.GPIO
	sudo pip3 install pyserial
	sudo pip3 install paho-mqtt
	```
7. Clone DataCollector files from github in **home/pi/**
	```
	git clone https://github.com/mfalfafa/Forwarder-system.git
	or
	git clone git://github.com/mfalfafa/Forwarder-system.git
	```
8. Edit file **/etc/profile** and add the following command
	```
	sudo python3 /home/pi/Forwarder-system/ready/DataCollector-v1.py
	```
9. Same as Forwarder
10. Same as Forwarder