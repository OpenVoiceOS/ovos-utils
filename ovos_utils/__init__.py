# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from threading import Thread
from time import sleep
import requests
import os
from os.path import isdir, join, dirname
import re
import socket
import datetime
import kthread
from inflection import camelize, titleize, transliterate, parameterize, \
    ordinalize


def ensure_mycroft_import():
    try:
        import mycroft
    except ImportError:
        import sys
        from ovos_utils import get_mycroft_root
        MYCROFT_ROOT_PATH = get_mycroft_root()
        if MYCROFT_ROOT_PATH is not None:
            sys.path.append(MYCROFT_ROOT_PATH)
        else:
            raise


def get_ip():
    # taken from https://stackoverflow.com/a/28950776/13703283
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_external_ip():
    return requests.get('https://api.ipify.org').text


def resolve_ovos_resource_file(res_name):
    """Convert a resource into an absolute filename.
    used internally for ovos resources
    """
    # First look for fully qualified file (e.g. a user setting)
    if os.path.isfile(res_name):
        return res_name

    # now look in bundled ovos resources
    filename = join(dirname(__file__), "res", res_name)
    if os.path.isfile(filename):
        return filename

    return None  # Resource cannot be resolved


def get_mycroft_root():
    paths = [
        "/opt/venvs/mycroft-core/lib/python3.7/site-packages/",  # mark1/2
        "/opt/venvs/mycroft-core/lib/python3.4/site-packages/ ",  # old mark1 installs
        "/home/pi/mycroft-core"  # picroft
    ]
    for p in paths:
        if isdir(join(p, "mycroft")):
            return p
    return None


def resolve_resource_file(res_name, root_path=None):
    """Convert a resource into an absolute filename.

    Resource names are in the form: 'filename.ext'
    or 'path/filename.ext'

    The system wil look for ~/.mycroft/res_name first, and
    if not found will look at /opt/mycroft/res_name,
    then finally it will look for res_name in the 'mycroft/res'
    folder of the source code package.

    Example:
    With mycroft running as the user 'bob', if you called
        resolve_resource_file('snd/beep.wav')
    it would return either '/home/bob/.mycroft/snd/beep.wav' or
    '/opt/mycroft/snd/beep.wav' or '.../mycroft/res/snd/beep.wav',
    where the '...' is replaced by the path where the package has
    been installed.

    Args:
        res_name (str): a resource path/name
    Returns:
        str: path to resource or None if no resource found
    """
    # TODO handle cyclic import
    from ovos_utils.configuration import read_mycroft_config
    config = read_mycroft_config()

    # First look for fully qualified file (e.g. a user setting)
    if os.path.isfile(res_name):
        return res_name

    # Now look for ~/.mycroft/res_name (in user folder)
    filename = os.path.expanduser("~/.mycroft/" + res_name)
    if os.path.isfile(filename):
        return filename

    # Next look for /opt/mycroft/res/res_name
    data_dir = os.path.expanduser(config['data_dir'])
    filename = os.path.expanduser(os.path.join(data_dir, res_name))
    if os.path.isfile(filename):
        return filename

    # look in ovos_utils package itself
    found = resolve_ovos_resource_file(res_name)
    if found:
        return found

    # Finally look for it in the source package
    paths = [
        "/opt/venvs/mycroft-core/lib/python3.7/site-packages/",  # mark1/2
        "/opt/venvs/mycroft-core/lib/python3.4/site-packages/ ",  # old mark1 installs
        "/home/pi/mycroft-core"  # picroft
    ]
    if root_path:
        paths += [root_path]
    for p in paths:
        filename = os.path.join(p, 'mycroft', 'res', res_name)
        filename = os.path.abspath(os.path.normpath(filename))
        if os.path.isfile(filename):
            return filename

    return None  # Resource cannot be resolved


def create_killable_daemon(target, args=(), kwargs=None, autostart=True):
    """Helper to quickly create and start a thread with daemon = True"""
    t = kthread.KThread(target=target, args=args, kwargs=kwargs)
    t.daemon = True
    if autostart:
        t.start()
    return t


def create_daemon(target, args=(), kwargs=None, autostart=True):
    """Helper to quickly create and start a thread with daemon = True"""
    t = Thread(target=target, args=args, kwargs=kwargs)
    t.daemon = True
    if autostart:
        t.start()
    return t


def create_loop(target, interval, args=(), kwargs=None):
    """
    Helper to quickly create and start a thread with daemon = True
    and repeat it every interval seconds
    """

    def loop(*args, **kwargs):
        try:
            while True:
                target(*args, **kwargs)
                sleep(interval)
        except KeyboardInterrupt:
            return

    return create_daemon(loop, args, kwargs)


def wait_for_exit_signal():
    """Blocks until KeyboardInterrupt is received"""
    try:
        while True:
            sleep(100)
    except KeyboardInterrupt:
        pass


def get_handler_name(handler):
    """Name (including class if available) of handler function.

    Arguments:
        handler (function): Function to be named

    Returns:
        string: handler name as string
    """
    if '__self__' in dir(handler) and 'name' in dir(handler.__self__):
        return handler.__self__.name + '.' + handler.__name__
    else:
        return handler.__name__


def camel_case_split(identifier: str) -> str:
    """Split camel case string"""
    regex = '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)'
    matches = re.finditer(regex, identifier)
    return ' '.join([m.group(0) for m in matches])


def rotate_list(l, n=1):
    return l[n:] + l[:n]


def datestr2ts(datestr):
    y = int(datestr[:4])
    m = int(datestr[4:6])
    d = int(datestr[-2:])
    dt = datetime.datetime(y, m, d)
    return dt.timestamp()
