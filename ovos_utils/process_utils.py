import sys
from collections import namedtuple
from enum import IntEnum
from dataclasses import dataclass


@dataclass
class RuntimeRequirements:
    # to ensure backwards compatibility the default values require internet before skill loading
    # skills in the wild may assume this behaviour and require network on initialization
    # any ovos aware skills should change these as appropriate

    # xxx_before_load is used by skills service
    network_before_load: bool = True
    internet_before_load: bool = True
    gui_before_load: bool = False

    # requires_xxx is currently purely informative and not consumed by core
    # this allows a skill to spec if it needs connectivity to handle utterances
    requires_internet: bool = True
    requires_network: bool = True
    requires_gui: bool = False

    # xxx_fallback is currently purely informative and not consumed by core
    # this allows a skill to spec if it has a fallback for temporary offline events, eg, by having a cache
    no_internet_fallback: bool = False
    no_network_fallback: bool = False
    no_gui_fallback: bool = True  # can work voice only


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
