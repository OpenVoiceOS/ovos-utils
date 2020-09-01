

# Run pulse on boot as root

bash script bellow to setup pulseaudio system service

 ```bash
echo "Creating pulseaudio system service"

if [ -f /etc/systemd/system/pulseaudio.service ]
then
    rm /etc/systemd/system/pulseaudio.service
fi

echo "[Unit]" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "Description=PulseAudio Daemon" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "[Install]" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "WantedBy=multi-user.target" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "[Service]" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "Type=simple" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "PrivateTmp=true" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null
echo "ExecStart=/usr/bin/pulseaudio --system --realtime --disallow-exit --no-cpu-limit" | sudo tee -a /etc/systemd/system/pulseaudio.service > /dev/null

chmod +x /etc/systemd/system/pulseaudio.service
systemctl enable pulseaudio.service

usermod -aG pulse pi
usermod -aG pulse-access pi

usermod -aG pulse root
usermod -aG pulse-access root

echo
echo 'Pulseaudio configuration complete'
echo

```


# Pulse tweaks

for docker
```bash
echo "load-module mload-module module-switch-on-connect auth-anonymous=1 port=34567" | sudo tee -a /etc/pulse/system.pa > /dev/null
```