#!/usr/bin/env python3
from subprocess import call


def ntp_sync():
    # Force the system clock to synchronize with internet time servers
    call('service ntp stop', shell=True)
    call('ntpd -gq', shell=True)
    call('service ntp start', shell=True)


def system_shutdown():
    # Turn the system completely off (with no option to inhibit it)
    call('sudo systemctl poweroff -i', shell=True)


def system_reboot():
    # Shut down and restart the system
    call('sudo systemctl reboot -i', shell=True)


def ssh_enable():
    # Permanently allow SSH access
    call('sudo systemctl enable ssh.service', shell=True)
    call('sudo systemctl start ssh.service', shell=True)


def ssh_disable():
    # Permanently block SSH access from the outside
    call('sudo systemctl stop ssh.service', shell=True)
    call('sudo systemctl disable ssh.service', shell=True)

