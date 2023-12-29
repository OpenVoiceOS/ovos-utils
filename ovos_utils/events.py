import time
from datetime import datetime, timedelta
from inspect import signature
from typing import Callable, Optional, Union

from ovos_utils.fakebus import Message, FakeBus, dig_for_message
from ovos_utils.file_utils import to_alnum
from ovos_utils.log import LOG


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


class EventSchedulerInterface:
    """Interface for accessing the event scheduler over the message bus."""

    def __init__(self, bus=None, skill_id=None):
        self.skill_id = skill_id or self.__class__.__name__.lower()
        self.bus = bus
        self.events = EventContainer(bus)
        self.scheduled_repeats = []

    def set_bus(self, bus):
        """Attach the messagebus of the parent skill

        Args:
            bus (MessageBusClient): websocket connection to the messagebus
        """
        self.bus = bus
        self.events.set_bus(bus)

    def set_id(self, skill_id: str):
        """
        Attach the skill_id of the parent skill

        Args:
            skill_id (str): skill_id of the parent skill
        """
        self.skill_id = skill_id

    def _get_source_message(self):
        message = dig_for_message() or Message("")
        message.context['skill_id'] = self.skill_id
        return message

    def _create_unique_name(self, name: str) -> str:
        """
        Return a name unique to this skill using the format [skill_id]:[name].
        @param name: Name to use internally
        @return name unique to this skill
        """
        # TODO: Is a null name valid or should it raise an exception?
        return self.skill_id + ':' + (name or '')

    def _schedule_event(self, handler: Callable[..., None],
                        when: Union[datetime, int, float],
                        data: Optional[dict],
                        name: Optional[str],
                        repeat_interval: Optional[Union[float, int]] = None,
                        context: Optional[dict] = None):
        """
        Underlying method for schedule_event and schedule_repeating_event.
        Takes scheduling information and sends it off on the message bus.
        @param handler: method to be called at the scheduled time(s)
        @param when: time (tzaware or default to system tz) or delta seconds to
            first call the handler
        @param data: Message data to send to `handler
        @param name: Event name, must be unique in the context of this object
        @param repeat_interval:  time in seconds between calls
        @param context: Message context to send to `handler`

        """
        if isinstance(when, (int, float)):
            if when < 0:
                raise ValueError(f"Expected datetime or positive int/float. "
                                 f"got: {when}")
            when = datetime.now() + timedelta(seconds=when)
        if not isinstance(when, datetime):
            raise TypeError(f"Expected datetime, int, or float but got: {when}")
        if not name:
            name = self.skill_id + handler.__name__
        unique_name = self._create_unique_name(name)
        if repeat_interval:
            self.scheduled_repeats.append(name)  # store "friendly name"

        data = data or {}

        def on_error(e):
            LOG.exception(f'An error occurred executing the scheduled event: '
                          f'{e}')

        wrapped = create_basic_wrapper(handler, on_error)
        self.events.add(unique_name, wrapped, once=not repeat_interval)
        event_data = {'time': when.timestamp(),  # Epoch timestamp
                      'event': unique_name,
                      'repeat': repeat_interval,
                      'data': data}

        message = self._get_source_message()
        context = context or message.context
        context["skill_id"] = self.skill_id
        self.bus.emit(Message('mycroft.scheduler.schedule_event',
                                                    data=event_data, context=context))

    def schedule_event(self, handler: Callable[..., None],
                       when: Union[datetime, int, float],
                       data: Optional[dict] = None,
                       name: Optional[str] = None,
                       context: Optional[dict] = None):
        """
        Schedule a single-shot event.
        @param handler: method to be called at the scheduled time(s)
        @param when: time (tzaware or default to system tz) or delta seconds
            to first call the handler
        @param data: Message data to send to `handler
        @param name: Event name, must be unique in the context of this object
        @param context: Message context to send to `handler`
        """
        self._schedule_event(handler, when, data, name, context=context)

    def schedule_repeating_event(self,
                                 handler: Callable[..., None],
                                 when: Optional[Union[datetime, int, float]],
                                 interval: Union[float, int],
                                 data: Optional[dict] = None,
                                 name: Optional[str] = None,
                                 context: Optional[dict] = None):
        """
        Schedule a repeating event.
        @param handler: method to be called at the scheduled time(s)
        @param when: time (tzaware or default to system tz) or delta seconds to
            first call the handler. If None, first call is in `repeat_interval`
        @param data: Message data to send to `handler
        @param name: Event name, must be unique in the context of this object
        @param interval:  time in seconds between calls
        @param context: Message context to send to `handler`
        """
        # Ensure name is defined to avoid re-scheduling
        name = name or self.skill_id + handler.__name__

        # Do not schedule if this event is already scheduled by the skill
        if name not in self.scheduled_repeats:
            # If only interval is given set to trigger in [interval] seconds
            # from now.
            if not when:
                when = datetime.now() + timedelta(seconds=interval)
            self._schedule_event(handler, when, data, name, interval, context)
        else:
            LOG.debug('The event is already scheduled, cancel previous '
                      'event if this scheduling should replace the last.')

    def update_scheduled_event(self, name: str, data: Optional[dict] = None):
        """
        Change data of event.

        Args:
            name (str): reference name of event (from original scheduling)
            data (dict): new data to update event with
        """
        data = {
            'event': self._create_unique_name(name),
            'data': data or {}
        }
        message = self._get_source_message()
        self.bus.emit(message.forward('mycroft.schedule.update_event', data))

    def cancel_scheduled_event(self, name: str):
        """
        Cancel a pending event. The event will no longer be scheduled.

        Args:
            name (str): reference name of event (from original scheduling)
        """
        unique_name = self._create_unique_name(name)
        data = {'event': unique_name}
        if name in self.scheduled_repeats:
            self.scheduled_repeats.remove(name)
        if self.events.remove(unique_name):
            message = self._get_source_message()
            self.bus.emit(message.forward('mycroft.scheduler.remove_event',
                                          data))

    def get_scheduled_event_status(self, name: str) -> int:
        """
        Get scheduled event data and return the amount of time left

        Args:
            name (str): reference name of event (from original scheduling)

        Returns:
            int: the time left in seconds

        Raises:
            Exception: Raised if event is not found
        """
        event_name = self._create_unique_name(name)
        data = {'name': event_name}

        reply_name = f'mycroft.event_status.callback.{event_name}'
        message = self._get_source_message()
        msg = message.forward('mycroft.scheduler.get_event', data)
        status = self.bus.wait_for_response(msg, reply_type=reply_name)

        if status:
            event_time = int(status.data[0][0])
            current_time = int(time.time())
            time_left_in_seconds = event_time - current_time
            LOG.info(time_left_in_seconds)
            return time_left_in_seconds
        else:
            raise Exception("Event Status Messagebus Timeout")

    def cancel_all_repeating_events(self):
        """
        Cancel any repeating events started by the skill.
        """
        # NOTE: Gotta make a copy of the list due to the removes that happen
        #       in cancel_scheduled_event().
        for e in list(self.scheduled_repeats):
            self.cancel_scheduled_event(e)

    def shutdown(self):
        """
        Shutdown the interface unregistering any event handlers.
        """
        self.cancel_all_repeating_events()
        self.events.clear()
