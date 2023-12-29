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
import datetime
import re
from functools import lru_cache, wraps
from threading import Thread, Event
from time import monotonic_ns, sleep

import kthread

from ovos_utils.log import LOG


def threaded_timeout(timeout=5):
    """
    Start a thread with a specified timeout. If timeout is exceeded, an
    exception is raised and the thread is terminated.
    Adapted from https://github.com/OpenJarbas/InGeo
    @param timeout: Timeout in seconds to wait before terminating the process
    """

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception(f'function [{func.__name__}] timeout '
                             f'[{timeout}] exceeded!')]

            def func_wrapped():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = Thread(target=func_wrapped)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret

        return wrapper

    return deco


class classproperty(property):
    """Decorator for a Class-level property.
    Credit to Denis Rhyzhkov on Stackoverflow: https://stackoverflow.com/a/13624858/1280629"""

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def timed_lru_cache(
        _func=None, *, seconds: int = 7000, maxsize: int = 128, typed: bool = False
):
    """ Extension over existing lru_cache with timeout

    taken from: https://blog.soumendrak.com/cache-heavy-computation-functions-with-a-timeout-value

    :param seconds: timeout value
    :param maxsize: maximum size of the cache
    :param typed: whether different keys for different types of cache keys
    """

    def wrapper_cache(f):
        # create a function wrapped with traditional lru_cache
        f = lru_cache(maxsize=maxsize, typed=typed)(f)
        # convert seconds to nanoseconds to set the expiry time in nanoseconds
        f.delta = seconds * 10 ** 9
        f.expiration = monotonic_ns() + f.delta

        @wraps(f)  # wraps is used to access the decorated function attributes
        def wrapped_f(*args, **kwargs):
            if monotonic_ns() >= f.expiration:
                # if the current cache expired of the decorated function then
                # clear cache for that function and set a new cache value with new expiration time
                f.cache_clear()
                f.expiration = monotonic_ns() + f.delta
            return f(*args, **kwargs)

        wrapped_f.cache_info = f.cache_info
        wrapped_f.cache_clear = f.cache_clear
        return wrapped_f

    # To allow decorator to be used without arguments
    if _func is None:
        return wrapper_cache
    else:
        return wrapper_cache(_func)


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
        Event().wait()
    except KeyboardInterrupt:
        LOG.debug(f"Exiting on KeyboardInterrupt")


def get_handler_name(*args, **kwargs):
    from ovos_utils.log import log_deprecation
    log_deprecation("Import from `ovos_utils.events`", "0.1.0")
    from ovos_utils.events import get_handler_name
    return get_handler_name(*args, **kwargs)


def camel_case_split(identifier: str) -> str:
    """Split camel case string"""
    regex = '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)'
    matches = re.finditer(regex, identifier)
    return ' '.join([m.group(0) for m in matches])


def rotate_list(l, n=1):
    return l[n:] + l[:n]


def flatten_list(some_list, tuples=True):
    _flatten = lambda l: [item for sublist in l for item in sublist]
    if tuples:
        while any(isinstance(x, list) or isinstance(x, tuple)
                  for x in some_list):
            some_list = _flatten(some_list)
    else:
        while any(isinstance(x, list) for x in some_list):
            some_list = _flatten(some_list)
    return some_list


def datestr2ts(datestr):
    y = int(datestr[:4])
    m = int(datestr[4:6])
    d = int(datestr[-2:])
    dt = datetime.datetime(y, m, d)
    return dt.timestamp()
