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
from os.path import isdir, join
import re
import datetime
import kthread
from ovos_utils.network_utils import get_ip, get_external_ip, is_connected_dns, is_connected_http, is_connected
from ovos_utils.file_utils import resolve_ovos_resource_file, resolve_resource_file


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

