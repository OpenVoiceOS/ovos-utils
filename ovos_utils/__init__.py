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
import warnings
from time import sleep

from ovos_utils.decorators import classproperty, timed_lru_cache
from ovos_utils.list_utils import flatten_list, rotate_list
from ovos_utils.log import LOG, log_deprecation
from ovos_utils.text_utils import camel_case_split
from ovos_utils.thread_utils import wait_for_exit_signal, threaded_timeout, create_killable_daemon, create_daemon


def create_loop(target, interval, args=(), kwargs=None):
    """
    Helper to quickly create and start a thread with daemon = True
    and repeat it every interval seconds
    """
    warnings.warn(
        "deprecated without replacement and will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    log_deprecation("deprecated without replacement", "2.0.0")

    def loop(*args, **kwargs):
        try:
            while True:
                target(*args, **kwargs)
                sleep(interval)
        except KeyboardInterrupt:
            return

    return create_daemon(loop, args, kwargs)


def datestr2ts(datestr):
    warnings.warn(
        "deprecated without replacement and will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    log_deprecation("deprecated without replacement", "2.0.0")

    y = int(datestr[:4])
    m = int(datestr[4:6])
    d = int(datestr[-2:])
    dt = datetime.datetime(y, m, d)
    return dt.timestamp()
