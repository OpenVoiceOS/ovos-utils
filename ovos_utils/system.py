import inspect
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from enum import Enum
from os.path import expanduser, exists, join

from ovos_utils.log import LOG


# TODO: Deprecate MycroftRootLocations in 0.1.0
class MycroftRootLocations(str, Enum):
    PICROFT = "/home/pi/mycroft-core"
    BIGSCREEN = "/home/mycroft/mycroft-core"
    OVOS = "/usr/lib/python3.9/site-packages"
    OLD_MARK1 = "/opt/venvs/mycroft-core/lib/python3.4/site-packages"
    MARK1 = "/opt/venvs/mycroft-core/lib/python3.7/site-packages"
    MARK2 = "/opt/mycroft"
    HOME = expanduser("~/mycroft-core")  # git clones


_USER_DEFINED_ROOT = None


def is_running_from_module(module_name):
    # Stack:
    # [0] - _log()
    # [1] - debug(), info(), warning(), or error()
    # [2] - caller
    stack = inspect.stack()

    # Record:
    # [0] - frame object
    # [1] - filename
    # [2] - line number
    # [3] - function
    # ...
    for record in stack[2:]:
        mod = inspect.getmodule(record[0])
        name = mod.__name__ if mod else ''
        # module name in file path of caller
        # or import name matches module name
        if f"/{module_name}/" in record[1] or \
                name.startswith(module_name.replace("-", "_").replace(" ", "_")):
            return True
    return False


# system utils
def ntp_sync():
    # Force the system clock to synchronize with internet time servers
    subprocess.call('service ntp stop', shell=True)
    subprocess.call('ntpd -gq', shell=True)
    subprocess.call('service ntp start', shell=True)


def system_shutdown(sudo=True):
    """
    Turn the system completely off (with no option to inhibit it)
    @param sudo: use sudo when calling systemctl
    """
    cmd = 'systemctl poweroff -i'
    if sudo:
        cmd = f'sudo {cmd}'
    subprocess.call(cmd, shell=True)


def system_reboot(sudo=True):
    """
    Shut down and restart the system
    @param sudo: use sudo when calling systemctl
    """
    cmd = 'systemctl reboot -i'
    if sudo:
        cmd = f'sudo {cmd}'
    subprocess.call(cmd, shell=True)


def ssh_enable(sudo=True, user=False):
    """
    Permanently allow SSH access
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    enable_service("ssh.service", sudo=sudo, user=user)


def ssh_disable(sudo=True, user=False):
    """
    Permanently block SSH access from the outside
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    disable_service("ssh.service", sudo=sudo, user=user)


def restart_mycroft_service(sudo=True, user=False):
    """
    Restarts the `mycroft.service` systemd service
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    restart_service("mycroft.service", sudo=sudo, user=user)


def restart_service(service_name, sudo=True, user=False):
    """
    Restarts a systemd service using systemctl
    @param service_name: name of service to restart
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    cmd = f'systemctl restart {service_name}'
    if user:
        cmd = f"{cmd} --user"
    elif sudo:
        cmd = f"sudo {cmd}"
    subprocess.call(cmd, shell=True)


def enable_service(service_name, sudo=False, user=False):
    """
    Enables and Starts a systemd service using systemctl
    @param service_name: name of service to Enable and Start
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    enable_command = f"systemctl enable {service_name}"
    start_command = f"systemctl start {service_name}"
    if user:
        enable_command = f"{enable_command} --user"
        start_command = f"{start_command} --user"
    elif sudo:
        enable_command = f"sudo {enable_command}"
        start_command = f"sudo {start_command}"
    subprocess.call(enable_command, shell=True)
    subprocess.call(start_command, shell=True)


def disable_service(service_name, sudo=False, user=False):
    """
    Disables and Stops a systemd service using systemctl
    @param service_name: name of service to Disable and Stop
    @param sudo: use sudo when calling systemctl
    @param user: pass --user flag when calling systemctl
    """
    disable_command = f"systemctl disable {service_name}"
    stop_command = f"systemctl stop {service_name}"
    if user:
        disable_command = f"{disable_command} --user"
        stop_command = f"{stop_command} --user"
    elif sudo:
        disable_command = f"sudo {disable_command}"
        stop_command = f"sudo {stop_command}"
    subprocess.call(stop_command, shell=True)
    subprocess.call(disable_command, shell=True)


def check_service_active(service_name, sudo=False, user=False) -> bool:
    """
    Checks if a systemd service is active using systemctl
    @param service_name: name of service to check
    @param user: pass --user flag when calling systemctl
    @param sudo: use sudo when calling systemctl
    @return: True if the service is active, else False
    """
    status_command = f"systemctl is-active --quiet {service_name}"
    if user:
        status_command = f"{status_command} --user"
    elif sudo:
        status_command = f"sudo {status_command}"
    state = subprocess.run(status_command, shell=True).returncode
    return state == 0


# platform fingerprinting
def set_root_path(path):
    global _USER_DEFINED_ROOT
    _USER_DEFINED_ROOT = path
    LOG.info(f"mycroft root set to {path}")


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
    # downstream wants to override the root location
    if _USER_DEFINED_ROOT:
        return _USER_DEFINED_ROOT
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
    # X server not running
    if not have_display:
        # raspberry pi specific check
        try:
            have_display = b"device_name=" in subprocess.check_output("tvservice -n 2>&1", shell=True)
        except Exception as e:
            pass
        
    # fallback check using matplotlib if available
    # seems to be foolproof and OS agnostic 
    # but do not want to drag the dependency
    if not have_display:
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


def module_property(func):
    """
    Decorator to turn module functions into properties.
    Function names must be prefixed with an underscore.
    :param func: function to decorate
    """
    import sys
    module = sys.modules[func.__module__]

    def fallback_getattr(name):
        raise AttributeError(
            f"module '{module.__name__}' has no attribute '{name}'")

    default_getattr = getattr(module, '__getattr__', fallback_getattr)

    def patched_getattr(name):
        if f'_{name}' == func.__name__:
            return func()
        return default_getattr(name)

    module.__getattr__ = patched_getattr
    return func

