import os
import subprocess
import re
import shutil
import sys
import sysconfig
from enum import Enum
import platform
import socket
from xdg import BaseDirectory as XDG
from os.path import expanduser, exists, join, isfile


class MycroftRootLocations(str, Enum):
    PICROFT = "/home/pi/mycroft-core"
    BIGSCREEN = "/home/mycroft/mycroft-core"
    OVOS = "/usr/lib/python3.9/site-packages"
    OLD_MARK1 = "/opt/venvs/mycroft-core/lib/python3.4/site-packages"
    MARK1 = "/opt/venvs/mycroft-core/lib/python3.7/site-packages"
    MARK2 = "/opt/mycroft"
    HOME = expanduser("~/mycroft-core")  # git clones


# system utils
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


# platform fingerprinting
def find_root_from_sys_path():
    """Find mycroft root folder from sys.path, eg. venv site-packages."""
    for p in [path for path in sys.path if path != '']:
        if exists(join(p, 'mycroft', 'configuration', 'mycroft.conf')):
            return p
    else:
        return None


def find_root_from_sitepackages():
    """Find root from system or venv's sitepackages."""
    site = sysconfig.get_paths()['platlib']
    if exists(join(site, 'mycroft', 'configuration', 'mycroft.conf')):
        return site
    else:
        return None


def search_mycroft_core_location():
    """Check python path (.venv), system packages and finally known mycroft
    locations."""
    # if we are in a .venv that should take precedence over everything else
    if find_root_from_sitepackages():
        return find_root_from_sitepackages()
    # if there is a system wide install that should take precedence over
    # hardcoded locations
    elif find_root_from_sys_path():
        return find_root_from_sys_path()
    # finally look at default locations
    for p in MycroftRootLocations:
        if os.path.isdir(p):
            return p
    return None


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
            if desktop_session in ["gnome", "unity", "cinnamon", "mate",
                                   "xfce4", "lxde", "fluxbox",
                                   "blackbox", "openbox", "icewm", "jwm",
                                   "afterstep", "trinity", "kde"]:
                return desktop_session
            # Special cases
            # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
            # There is no guarantee that they will not do the same with the other desktop environments.
            elif "xfce" in desktop_session or desktop_session.startswith(
                    "xubuntu"):
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
        if re.search(process, x.decode("utf-8")):
            return True
    return False


def find_executable(executable):
    return shutil.which(executable)


def is_installed(executable):
    return bool(find_executable(executable))


def has_screen():
    have_display = "DISPLAY" in os.environ
    if not have_display:
        # fallback check using matplotlib if available
        try:
            import matplotlib.pyplot as plt
            try:
                plt.figure()
                have_display = True
            except:
                have_display = False
        except ImportError:
            pass
    return have_display


def get_platform_fingerprint():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "system": platform.system(),
        "version": platform.version(),
        "arch": platform.machine(),
        "release": platform.release(),
        "desktop_env": get_desktop_environment(),
        "mycroft_core_location": search_mycroft_core_location(),
        "can_display": has_screen(),
        "is_gui_installed": is_installed("mycroft-gui-app"),
        "is_vlc_installed": is_installed("vlc"),
        "pulseaudio_running": is_process_running("pulseaudio"),
        "core_supports_xdg": core_supports_xdg(),
        "core_version": {
            "version_str": get_mycroft_version(),
            "is_chatterbox_core": is_chatterbox_core(),
            "is_neon_core": is_neon_core(),
            "is_holmes": is_holmes(),
            "is_ovos": is_ovos(),
            "is_mycroft_core": is_mycroft_core()
        }
    }


def get_mycroft_version():
    try:
        from mycroft.version import CORE_VERSION_STR
        return CORE_VERSION_STR
    except:
        pass

    root = search_mycroft_core_location()
    if root:
        version_file = join(root, "version", "__init__.py")
        if not isfile(version_file):
            version_file = join(root, "mycroft", "version", "__init__.py")
        if isfile(version_file):
            version = []
            with open(version_file) as f:
                text = f.read()
                version.append(
                    text.split("CORE_VERSION_MAJOR =")[-1].split("\n")[0].strip())
                version.append(
                    text.split("CORE_VERSION_MINOR =")[-1].split("\n")[0].strip())
                version.append(
                    text.split("CORE_VERSION_BUILD =")[-1].split("\n")[0].strip())
                version = ".".join(version)
                if "CORE_VERSION_STR = '.'.join(map(str, " \
                   "CORE_VERSION_TUPLE)) + " in text:
                    version += text.split(
                        "CORE_VERSION_STR = '.'.join(map(str, "
                        "CORE_VERSION_TUPLE)) + ")[-1].split("\n")[0][1:-1]
                return version
        return None


def is_chatterbox_core():
    try:
        import chatterbox
        return True
    except ImportError:
        return False


def is_neon_core():
    try:
        import neon_core
        return True
    except ImportError:
        return False


def is_mycroft_core():
    try:
        import mycroft
        return True
    except ImportError:
        return False


def is_holmes():
    return "HolmesV" in (get_mycroft_version() or "")


def is_ovos():
    return "OpenVoiceOS" in (get_mycroft_version() or "")


def core_supports_xdg():
    if any((is_holmes(), is_ovos(), is_neon_core(), is_chatterbox_core())):
        return True
    # mycroft-core does not support XDG as of 10 may 2021
    # however there are patched versions out there, eg, alpine package
    # check if the .conf exists in new location
    # TODO deprecate
    return isfile(join(XDG.save_config_path('mycroft'), 'mycroft.conf'))
