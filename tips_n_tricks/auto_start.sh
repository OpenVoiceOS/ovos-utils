#!/usr/bin/env bash
echo
echo 'Starting creation of Mycroft AI background service'
echo


if [ -f /etc/systemd/system/mycroft.service ]
then
	sudo rm /etc/systemd/system/mycroft.service
fi

echo "[Unit]" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "Description=Mycroft AI" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "[Service]" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "WorkingDirectory=/home/pi/mycroft-core" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "ExecStart=/bin/bash /home/pi/startup.sh" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "Type=forking" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "[Install]" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null
echo "WantedBy=multi-user.target" | sudo tee -a /etc/systemd/system/mycroft.service > /dev/null

chmod +x /etc/systemd/system/mycroft.service
systemctl enable mycroft.service

echo
echo 'Creation of Mycroft AI background service complete'
echo