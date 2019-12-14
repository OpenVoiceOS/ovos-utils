#!/usr/bin/env python3
import sys
import os
import subprocess
import re


def get_desktop_environment():
    # From http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=1139057
    if sys.platform in ["win32", "cygwin"]:
        return "windows"
    elif sys.platform == "darwin":
        return "mac"
    else:  # Most likely either a POSIX system or something not much common
        desktop_session = os.environ.get("DESKTOP_SESSION")
        if desktop_session is not None:  # easier to match if we doesn't have  to deal with character cases
            desktop_session = desktop_session.lower()
            if desktop_session in ["gnome", "unity", "cinnamon", "mate", "xfce4", "lxde", "fluxbox",
                                   "blackbox", "openbox", "icewm", "jwm", "afterstep", "trinity", "kde"]:
                return desktop_session
            # Special cases
            # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
            # There is no guarantee that they will not do the same with the other desktop environments.
            elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
                return "xfce4"
            elif desktop_session.startswith("ubuntu"):
                return "unity"
            elif desktop_session.startswith("lubuntu"):
                return "lxde"
            elif desktop_session.startswith("kubuntu"):
                return "kde"
            elif desktop_session.startswith("razor"):  # e.g. razorkwin
                return "razor-qt"
            elif desktop_session.startswith("wmaker"):  # e.g. wmaker-common
                return "windowmaker"
        if os.environ.get('KDE_FULL_SESSION') == 'true':
            return "kde"
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            if not "deprecated" in os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                return "gnome2"
        # From http://ubuntuforums.org/showthread.php?t=652320
        elif is_process_running("xfce-mcs-manage"):
            return "xfce4"
        elif is_process_running("ksmserver"):
            return "kde"
        elif is_process_running("icewm"):
            return "icewm"
        elif is_process_running("fluxbox"):
            return "fluxbox"
        elif is_process_running("jwm"):
            return "jwm"
    return "unknown"


def is_process_running(process):
    # From http://www.bloggerpolis.com/2011/05/how-to-check-if-a-process-is-running-using-python/
    # and http://richarddingwall.name/2009/06/18/windows-equivalents-of-ps-and-kill-commands/
    try:  # Linux/Unix
        s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    except:  # Windows
        s = subprocess.Popen(["tasklist", "/v"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return True
    return False


def ntp_sync():
    # Force the system clock to synchronize with internet time servers
    subprocess.call('service ntp stop', shell=True)
    subprocess.call('ntpd -gq', shell=True)
    subprocess.call('service ntp start', shell=True)


def system_shutdown():
    # Turn the system completely off (with no option to inhibit it)
    subprocess.call('sudo systemctl poweroff -i', shell=True)


def system_reboot():
    # Shut down and restart the system
    subprocess.call('sudo systemctl reboot -i', shell=True)


def ssh_enable():
    # Permanently allow SSH access
    subprocess.call('sudo systemctl enable ssh.service', shell=True)
    subprocess.call('sudo systemctl start ssh.service', shell=True)


def ssh_disable():
    # Permanently block SSH access from the outside
    subprocess.call('sudo systemctl stop ssh.service', shell=True)
    subprocess.call('sudo systemctl disable ssh.service', shell=True)

