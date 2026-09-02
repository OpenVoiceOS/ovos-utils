import time
from datetime import datetime, timedelta
from inspect import signature
from typing import Callable, Optional, Union

from ovos_utils.fakebus import FakeMessage as Message, FakeBus, dig_for_message
from ovos_utils.file_utils import to_alnum
from ovos_utils.log import LOG
from ovos_utils.time import now_local, get_config_tz


def unmunge_message(message, skill_id: str):
    """
    Restore message keywords by removing the Letterified skill ID.
    Args:
        message (Message): Intent result message
        skill_id (str): skill identifier
    Returns:
        Message without clear keywords
    """
    if isinstance(message, Message) and \
            isinstance(message.data, dict):
        skill_id = to_alnum(skill_id)
        for key in list(message.data.keys()):
            if key.startswith(skill_id):
                # replace the munged key with the real one
                new_key = key[len(skill_id):]
                message.data[new_key] = message.data.pop(key)

    return message


def get_handler_name(handler: Callable) -> str:
    """
    Name (including class if available) of handler function.

    Args:
        handler (function): Function to be named

    Returns:
        string: handler name as string
    """
    if '__self__' in dir(handler) and 'name' in dir(handler.__self__):
        return handler.__self__.name + '.' + handler.__name__
    else:
        return handler.__name__


def create_wrapper(handler: Callable[..., None],
                   skill_id: str,
                   on_start: Callable[..., None],
                   on_end: Callable[..., None],
                   on_error: Callable[..., None]) \
        -> Callable[..., None]:
    """
    Create the default skill handler wrapper.
    This wrapper handles things like metrics, reporting handler start/stop
    and errors.

    @param handler: method/function to call
    @param skill_id: skill_id for associated skill
    @param on_start: function to call before executing the handler. Called
        optionally with the Message
    @param on_end: function to call after executing the handler
    @param on_error: function to call for error reporting. Called with the
        exception, and optionally the Message associated with the exception
    @return: callable implementing the passed methods
    """

    def wrapper(message):
        try:
            message = unmunge_message(message, skill_id)
            if on_start:
                on_start(message)

            if len(signature(handler).parameters) == 0:
                handler()
            else:
                handler(message)

        except Exception as e:
            if on_error:
                if len(signature(on_error).parameters) == 2:
                    on_error(e, message)
                else:
                    on_error(e)
        finally:
            if on_end:
                on_end(message)

    return wrapper


def create_basic_wrapper(handler: Callable[..., None],
                         on_error: Optional[Callable[[Exception],
                         None]] = None) -> \
        Callable[..., None]:
    """
    Create the default skill handler wrapper.

    This wrapper handles things like metrics, reporting handler start/stop
    and errors.

    Arguments:
        handler (callable): method/function to call
        on_error (function): function to call to report error.

    Returns:
        Wrapped callable
    """

    def wrapper(message):
        try:
            if len(signature(handler).parameters) == 0:
                handler()
            else:
                handler(message)
        except Exception as e:
            LOG.exception(e)
            if on_error:
                on_error(e)

    return wrapper


class EventContainer:
    """
    Container tracking messagebus handlers.

    This container tracks events added by a skill, allowing unregistering
    all events on shutdown.
    """

    def __init__(self, bus=None):
        self.bus = bus or FakeBus()
        self.events = []

    def set_bus(self, bus):
        self.bus = bus

    def add(self, name: str, handler: Callable[..., None],
            once: bool = False):
        """
        Create event handler for executing intent or other event.
        @param name: Event (Message.msg_type) to register
        @param handler: Callback method to register to `name`
        @param once: If true, only call `handler` once
        """

        def once_wrapper(message):
            # Remove registered one-time handler before invoking,
            # allowing them to re-schedule themselves.
            self.remove(name)
            handler(message)

        if handler:
            if once:
                self.bus.once(name, once_wrapper)
                self.events.append((name, once_wrapper))
            else:
                self.bus.on(name, handler)
                self.events.append((name, handler))

            LOG.debug(f'Added event: {name}')

    def remove(self, name: str) -> bool:
        """
        Removes an event from bus emitter and events list.
        @param name: vent (Message.msg_type) to remove
        @return: True if found and removed, False if not found
        """
        LOG.debug(f"Removing event {name}")
        removed = False
        for _name, _handler in list(self.events):
            if name == _name:
                try:
                    self.events.remove((_name, _handler))
                except ValueError:
                    LOG.error(f'Failed to remove event {name}')
                    pass
                removed = True

        # Because of function wrappers, the emitter doesn't always directly
        # hold the _handler function, it sometimes holds something like
        # 'wrapper(_handler)'.  So a call like:
        #     self.bus.remove(_name, _handler)
        # will not find it, leaving an event handler with that name left behind
        # waiting to fire if it is ever re-installed and triggered.
        # Remove all handlers with the given name, regardless of handler.
        if removed:
            self.bus.remove_all_listeners(name)
        return removed

    def __iter__(self):
        return iter(self.events)

    def clear(self):
        """
        Unregister all registered handlers and clear the list of registered
        events.
        """
        for e, f in self.events:
            self.bus.remove(e, f)
        self.events = []  # Remove reference to wrappers
