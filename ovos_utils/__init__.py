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
import dataclasses
import datetime
import json
import warnings
from time import sleep
from typing import Dict, Any

from ovos_utils.decorators import classproperty, timed_lru_cache
from ovos_utils.list_utils import flatten_list, rotate_list
from ovos_utils.log import LOG, log_deprecation
from ovos_utils.text_utils import camel_case_split
from ovos_utils.thread_utils import wait_for_exit_signal, threaded_timeout, create_killable_daemon, create_daemon

try:
    import orjson
except ImportError:
    orjson = None


def json_dumps(payload: Any) -> str:
    """
    Serializes an object to a JSON string using `orjson` if available,
    with a fallback to the standard `json` library.

    This function provides a significant performance boost when `orjson` is
    installed, while ensuring compatibility by gracefully falling back. It also
    handles dataclass serialization for both implementations.

    Args:
        payload (Any): The object to be serialized. This can be a built-in
                       type, a dictionary, or a dataclass instance.

    Returns:
        str: The serialized JSON string.
    """
    if orjson is None:
        # handle dataclasses
        if dataclasses.is_dataclass(payload):
            payload = dataclasses.asdict(payload)
        return json.dumps(payload, ensure_ascii=False)
    else:
        # orjson.dumps has native dataclass support and returns bytes
        return orjson.dumps(payload).decode("utf-8")


def json_loads(payload: str) -> Dict[str, Any]:
    """
    Deserializes a JSON string into a dictionary using `orjson` if available,
    with a fallback to the standard `json` library.

    This function provides a significant performance boost for deserialization
    when `orjson` is installed.

    Args:
        payload (str): The JSON string to be deserialized.

    Returns:
        Dict[str, Any]: The deserialized data as a dictionary.
    """
    if orjson is None:
        return json.loads(payload)
    else:
        return orjson.loads(payload)


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
