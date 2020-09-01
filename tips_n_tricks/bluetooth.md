
# install


## alsa

```bash
sudo apt install bluealsa
```

## pulseaudio 

```bash
sudo apt-get install pulseaudio-module-bluetooth 
```
make auto connect

```bash
echo "load-module module-switch-on-connect" | sudo tee -a /etc/pulse/system.pa > /dev/null
```

# add user pi to bluetooth group

```bash
pi@raspberrypi:~ $ sudo adduser pi bluetooth
```

# disable raspi soundcard

I'm assuming that you don't use external analog speakers plug into the 3.5 mm jack. If this is true, let's disable alsa

This avoids soundcard being selected by default, if bluetooth is the only 
speaker it makes your life easier


```bash
sudo nano /boot/config.txt
```

Page down to the bottom of the file and look for two lines that read:

```
# Enable audio (loads snd_bcm2835)
dtparam=audio=on

```
and change to
```
# Enable audio (loads snd_bcm2835)
#dtparam=audio=on
```

# Edit the bluetooth unit file to stop loading the SIM profile. 

A failed attempt at loading the nonexistent SIM access profile (sap) is being made. 

This will get rid of the sap related error messages, but it is not mandatory. 

Everything will still work without changing the unit file.

```bash
sudo nano /lib/systemd/system/bluetooth.service
```

 ```        
[Unit]
Description=Bluetooth service
Documentation=man:bluetoothd(8)
ConditionPathIsDirectory=/sys/class/bluetooth

[Service]
Type=dbus
BusName=org.bluez
ExecStart=/usr/lib/bluetooth/bluetoothd
NotifyAccess=main
#WatchdogSec=10
#Restart=on-failure
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
LimitNPROC=1
ProtectHome=true
ProtectSystem=full

[Install]
WantedBy=bluetooth.target
Alias=dbus-org.bluez.service
```

change

```
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap
```

# Connect to speaker

```bash
pi@raspberrypi:~ $ sudo bluetoothctl 
 ```  
 
after connecting and trusting the device it will auto connect on boot

```  
[NEW] Controller B8:27:EB:C3:57:51 raspberrypi [default]
[NEW] Device 11:11:11:11:11:11 MY_SPEAKER
[bluetooth]# scan on  
[bluetooth]# pair 11:11:11:11:11:11  
[bluetooth]# trust 11:11:11:11:11:11  
[bluetooth]# connect 11:11:11:11:11:11  
[bluetooth]# scan off
[bluetooth]# quit
```


