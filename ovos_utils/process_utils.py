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


import os
import sys
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from threading import Event
from time import sleep, monotonic

from ovos_utils.file_utils import get_temp_path
from ovos_utils.log import LOG


@dataclass
class RuntimeRequirements:
    # to ensure backwards compatibility the default values require internet before skill loading
    # skills in the wild may assume this behaviour and require network on initialization
    # any ovos aware skills should change these as appropriate

    # xxx_before_load is used by skills service
    network_before_load: bool = True
    internet_before_load: bool = True
    gui_before_load: bool = False

    # this allows a skill/plugin to spec if it needs connectivity to handle utterances
    requires_internet: bool = True
    requires_network: bool = True
    requires_gui: bool = False

    # this allows a skill/plugin to spec if it has a fallback for temporary offline events, eg, by having a cache
    no_internet_fallback: bool = False
    no_network_fallback: bool = False
    no_gui_fallback: bool = True  # can work voice only


class MonotonicEvent(Event):
    """Event class with monotonic timeout.

    Normal Event doesn't do wait timeout in a monotonic manner and may be
    affected by changes in system time. This class wraps the Event class
    wait() method with logic guards ensuring monotonic operation.
    """

    def wait_timeout(self, timeout):
        """Handle timeouts in a monotonic way.

        Repeatingly wait as long the event hasn't been set and the
        monotonic time doesn't indicate a timeout.

        Args:
            timeout: timeout of wait in seconds

        Returns:
            True if Event has been set, False if timeout expired
        """
        result = False
        end_time = monotonic() + timeout

        while not result and (monotonic() < end_time):
            # Wait however many seconds are left until the timeout has passed
            sleep(0.1)  # Mainly a precaution to not busy wait
            remaining_time = end_time - monotonic()
            LOG.debug('Will wait for {} sec for Event'.format(remaining_time))
            result = super().wait(remaining_time)

        return result

    def wait(self, timeout=None):
        if timeout is None:
            ret = super().wait()
        else:
            ret = self.wait_timeout(timeout)
        return ret


class ProcessState(IntEnum):
    """Oredered enum to make state checks easy.

    For example Alive can be determined using >= ProcessState.ALIVE,
    which will return True if the state is READY as well as ALIVE.
    """
    NOT_STARTED = 0
    STARTED = 1
    ERROR = 2
    STOPPING = 3
    ALIVE = 4
    READY = 5


# Process state change callback mappings.
_STATUS_CALLBACKS = [
    'on_started',
    'on_alive',
    'on_ready',
    'on_error',
    'on_stopping',
]

# namedtuple defaults only available on 3.7 and later python versions
if sys.version_info < (3, 7):
    StatusCallbackMap = namedtuple('CallbackMap', _STATUS_CALLBACKS)
    StatusCallbackMap.__new__.__defaults__ = (None,) * 5
else:
    StatusCallbackMap = namedtuple(
        'CallbackMap',
        _STATUS_CALLBACKS,
        defaults=(None,) * len(_STATUS_CALLBACKS),
    )


class ProcessStatus:
    """Process status tracker.

    The class tracks process status and execute callback methods on
    state changes as well as replies to messagebus queries of the
    process status.

    Args:
        name (str): process name, will be used to create the messagebus
                    messagetype "mycroft.{name}...".
        bus (MessageBusClient): Connection to the Mycroft messagebus.
        callback_map (StatusCallbackMap): optionally, status callbacks for the
                                          various status changes.
    """

    def __init__(self, name, bus=None, callback_map=None, namespace="mycroft"):
        self.name = name
        self._namespace = namespace
        self.callbacks = callback_map or StatusCallbackMap()
        self.state = ProcessState.NOT_STARTED

        # Messagebus connection
        self.bus = None
        if bus:
            self.bind(bus)

    def bind(self, bus):
        self.bus = bus
        self._register_handlers()

    def _register_handlers(self):
        """Register messagebus handlers for status queries."""
        self.bus.on(f'{self._namespace}.{self.name}.is_alive', self.check_alive)
        self.bus.on(f'{self._namespace}.{self.name}.is_ready', self.check_ready)

        # The next one is for backwards compatibility
        self.bus.on(f'mycroft.{self.name}.all_loaded', self.check_ready)

    def check_alive(self, message=None):
        """Respond to is_alive status request.

        Args:
            message: Optional message to respond to, if omitted no message
                     is sent.

        Returns:
            bool, True if process is alive.
        """
        is_alive = self.state >= ProcessState.ALIVE

        if message:
            status = {'status': is_alive}
            self.bus.emit(message.response(data=status))

        return is_alive

    def check_ready(self, message=None):
        """Respond to all_loaded status request.

        Args:
            message: Optional message to respond to, if omitted no message
                     is sent.

        Returns:
            bool, True if process is ready.
        """
        is_ready = self.state >= ProcessState.READY
        if message:
            status = {'status': is_ready}
            self.bus.emit(message.response(data=status))

        return is_ready

    def set_started(self):
        """Process is started."""
        self.state = ProcessState.STARTED
        if self.callbacks.on_started:
            self.callbacks.on_started()

    def set_alive(self):
        """Basic loading is done."""
        self.state = ProcessState.ALIVE
        if self.callbacks.on_alive:
            self.callbacks.on_alive()

    def set_ready(self):
        """All loading is done."""
        self.state = ProcessState.READY
        if self.callbacks.on_ready:
            self.callbacks.on_ready()

    def set_stopping(self):
        """Process shutdown has started."""
        self.state = ProcessState.STOPPING
        if self.callbacks.on_stopping:
            self.callbacks.on_stopping()

    def set_error(self, err=''):
        """An error has occured and the process is non-functional."""
        # Intentionally leave is_started True
        self.state = ProcessState.ERROR
        if self.callbacks.on_error:
            self.callbacks.on_error(err)


class Signal:
    """
    Capture and replace a signal handler with a user supplied function.
    The user supplied function is always called first then the previous
    handler, if it exists, will be called.  It is possible to chain several
    signal handlers together by creating multiply instances of objects of
    this class, providing a  different user functions for each instance.  All
    provided user functions will be called in LIFO order.
    """

    #
    # Constructor
    # Get the previous handler function then set the passed function
    # as the new handler function for this signal

    def __init__(self, sig_value, func):
        """
        Create an instance of the signal handler class.

        sig_value:  The ID value of the signal to be captured.
        func:  User supplied function that will act as the new signal handler.
        """
        super(Signal, self).__init__()  # python 3+ 'super().__init__()

        from signal import signal, SIG_DFL, default_int_handler, SIG_IGN

        self.__sig_value = sig_value
        self.__user_func = func  # store user passed function
        self.__previous_func = signal(sig_value, self)
        self.__previous_func = {  # Convert signal codes to functions
            SIG_DFL: default_int_handler,
            SIG_IGN: lambda a, b: None
        }.get(self.__previous_func, self.__previous_func)

    #
    # Called to handle the passed signal
    def __call__(self, signame, sf):
        """
        Allows the instance of this class to be called as a function.
        When called it runs the user supplied signal handler than
        checks to see if there is a previously defined handler.  If
        there is a previously defined handler call it.
        """
        self.__user_func()
        self.__previous_func(signame, sf)

    #
    # reset the signal handler
    def __del__(self):
        """
        Class destructor.  Called during garbage collection.
        Resets the signal handler to the previous function.
        """

        from signal import signal
        signal(self.__sig_value, self.__previous_func)


class PIDLock:  # python 3+ 'class Lock'

    """
    Create and maintains the PID lock file for this application process.
    The PID lock file is located in /tmp/mycroft/*.pid.  If another process
    of the same type is started, this class will 'attempt' to stop the
    previously running process and then change the process ID in the lock file.
    """

    @classmethod
    def init(cls):
        # TODO: Path to deprecation
        try:
            from ovos_config.meta import get_xdg_base
            base_dir = get_xdg_base()
        except ImportError:
            LOG.warning("ovos-config not available, using default "
                        "'mycroft' basedir")
            base_dir = "mycroft"
        cls.DIRECTORY = cls.DIRECTORY or get_temp_path(base_dir)

    #
    # Class constants
    DIRECTORY = None
    FILE = '/{}.pid'

    #
    # Constructor
    def __init__(self, service):
        """
        Builds the instance of this object.  Holds the lock until the
        object is garbage collected.

        service: Text string.  The name of the service application
        to be locked (ie: skills, voice)
        """
        PIDLock.init()
        super(PIDLock, self).__init__()  # python 3+ 'super().__init__()'
        self.__pid = os.getpid()  # PID of this application
        self.path = PIDLock.DIRECTORY + PIDLock.FILE.format(service)
        self.set_handlers()  # set signal handlers
        self.create()

    #
    # Reset the signal handlers to the 'delete' function
    def set_handlers(self):
        """
        Trap both SIGINT and SIGTERM to gracefully clean up PID files
        """
        from signal import SIGINT, SIGTERM
        self.__handlers = {SIGINT: Signal(SIGINT, self.delete),
                           SIGTERM: Signal(SIGTERM, self.delete)}

    #
    # Check to see if the PID already exists
    #  If it does exits perform several things:
    #    Stop the current process
    #    Delete the exiting file
    def exists(self):
        """
        Check if the PID lock file exists.  If it does
        then send a SIGKILL signal to the process defined by the value
        in the lock file.  Catch the keyboard interrupt exception to
        prevent propagation if stopped by use of Ctrl-C.
        """
        if not os.path.isfile(self.path):
            return
        with open(self.path, 'r') as L:
            try: # TODO - make it work in windows ?
                from signal import SIGKILL
                os.kill(int(L.read()), SIGKILL)
            except Exception as e:
                LOG.error(f"Failed to kill PID {L}: {e}")

    #
    # Create a lock file for this server process
    def touch(self):
        """
        If needed, create the '/tmp/mycroft' directory than open the
        lock file for writing and store the current process ID (PID)
        as text.
        """
        os.makedirs(PIDLock.DIRECTORY, exist_ok=True)
        with open(self.path, 'w') as L:
            L.write('{}'.format(self.__pid))

    #
    # Create the PID file
    def create(self):
        """
        Checks to see if a lock file for this service already exists,
        if so have it killed.  In either case write the process ID of
        the current service process to to the existing or newly created
        lock file in /tmp/mycroft/
        """
        self.exists()  # check for current running process
        self.touch()

    #
    # Delete the PID file - but only if it has not been overwritten
    # by a duplicate service application
    def delete(self, *args):
        """
        If the PID lock file contains the PID of this process delete it.

        *args: Ignored.  Required as this fuction is called as a signel
        handler.
        """
        try:
            with open(self.path, 'r') as L:
                pid = int(L.read())
                if self.__pid == pid:
                    os.unlink(self.path)
        except IOError:
            pass


def reset_sigint_handler():
    """Reset the sigint handler to the default.

    This fixes KeyboardInterrupt not getting raised when started via
    start-mycroft.sh
    """
    from signal import signal, SIGINT, default_int_handler
    signal(SIGINT, default_int_handler)
