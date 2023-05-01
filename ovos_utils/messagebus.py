import json
import time
from copy import deepcopy
from inspect import signature
from threading import Event

# from ovos_utils.configuration import read_mycroft_config, get_default_lang
from pyee import BaseEventEmitter

from ovos_utils import create_loop
from ovos_utils.json_helper import merge_dict
from ovos_utils.log import LOG
from ovos_utils.metrics import Stopwatch

_DEFAULT_WS_CONFIG = {"host": "0.0.0.0",
                      "port": 8181,
                      "route": "/core",
                      "ssl": False}


def dig_for_message():
    try:
        from ovos_bus_client.message import dig_for_message as _dig
        return _dig()
    except ImportError:
        pass
    return None


class FakeBus:
    def __init__(self, *args, **kwargs):
        self.started_running = False
        self.ee = kwargs.get("emitter") or BaseEventEmitter()
        self.ee.on("error", self.on_error)
        self.on_open()

    def on(self, msg_type, handler):
        self.ee.on(msg_type, handler)

    def once(self, msg_type, handler):
        self.ee.once(msg_type, handler)

    def emit(self, message):
        self.ee.emit("message", message.serialize())
        self.ee.emit(message.msg_type, message)

    def wait_for_message(self, message_type, timeout=3.0):
        """Wait for a message of a specific type.

        Arguments:
            message_type (str): the message type of the expected message
            timeout: seconds to wait before timeout, defaults to 3

        Returns:
            The received message or None if the response timed out
        """
        received_event = Event()
        received_event.clear()

        msg = None

        def rcv(m):
            nonlocal msg
            msg = m
            received_event.set()

        self.ee.once(message_type, rcv)
        received_event.wait(timeout)
        return msg

    def wait_for_response(self, message, reply_type=None, timeout=3.0):
        """Send a message and wait for a response.

        Arguments:
            message (Message): message to send
            reply_type (str): the message type of the expected reply.
                              Defaults to "<message.msg_type>.response".
            timeout: seconds to wait before timeout, defaults to 3

        Returns:
            The received message or None if the response timed out
        """
        reply_type = reply_type or message.msg_type + ".response"
        received_event = Event()
        received_event.clear()

        msg = None

        def rcv(m):
            nonlocal msg
            msg = m
            received_event.set()

        self.ee.once(reply_type, rcv)
        self.emit(message)
        received_event.wait(timeout)
        return msg

    def remove(self, msg_type, handler):
        try:
            self.ee.remove_listener(msg_type, handler)
        except:
            pass

    def remove_all_listeners(self, event_name):
        self.ee.remove_all_listeners(event_name)

    def create_client(self):
        return self

    def on_error(self, error):
        LOG.error(error)

    def on_open(self):
        pass

    def on_close(self):
        pass

    def run_forever(self):
        self.started_running = True

    def run_in_thread(self):
        self.run_forever()

    def close(self):
        self.on_close()


class _MutableMessage(type):
    """ To override isinstance checks we need to use a metaclass """

    def __instancecheck__(self, instance):
        try:
            from ovos_bus_client.message import Message as _MycroftMessage
            if isinstance(instance, _MycroftMessage):
                return True
        except:
            pass
        try:
            from mycroft_bus_client.message import Message as _MycroftMessage
            if isinstance(instance, _MycroftMessage):
                return True
        except:
            pass
        return super().__instancecheck__(instance)


# fake Message object to allow usage without ovos-bus-client installed
class FakeMessage(metaclass=_MutableMessage):
    """ fake Message object to allow usage with FakeBus without ovos-bus-client installed"""

    def __new__(cls, *args, **kwargs):
        try:  # most common case
            from ovos_bus_client import Message as _M
            return _M(*args, **kwargs)
        except:
            pass
        try:  # some old install that upgraded during migration period
            from mycroft_bus_client import Message as _M
            return _M(*args, **kwargs)
        except:  # FakeMessage
            return super().__new__(cls)

    def __init__(self, msg_type, data=None, context=None):
        """Used to construct a message object

        Message objects will be used to send information back and forth
        between processes of mycroft service, voice, skill and cli
        """
        self.msg_type = msg_type
        self.data = data or {}
        self.context = context or {}

    def __eq__(self, other):
        try:
            return other.msg_type == self.msg_type and \
                other.data == self.data and \
                other.context == self.context
        except:
            return False

    def serialize(self):
        """This returns a string of the message info.

        This makes it easy to send over a websocket. This uses
        json dumps to generate the string with type, data and context

        Returns:
            str: a json string representation of the message.
        """
        return json.dumps({'type': self.msg_type,
                           'data': self.data,
                           'context': self.context})

    @staticmethod
    def deserialize(value):
        """This takes a string and constructs a message object.

        This makes it easy to take strings from the websocket and create
        a message object.  This uses json loads to get the info and generate
        the message object.

        Args:
            value(str): This is the json string received from the websocket

        Returns:
            FakeMessage: message object constructed from the json string passed
            int the function.
            value(str): This is the string received from the websocket
        """
        obj = json.loads(value)
        return FakeMessage(obj.get('type') or '',
                           obj.get('data') or {},
                           obj.get('context') or {})

    def forward(self, msg_type, data=None):
        """ Keep context and forward message

        This will take the same parameters as a message object but use
        the current message object as a reference.  It will copy the context
        from the existing message object.

        Args:
            msg_type (str): type of message
            data (dict): data for message

        Returns:
            FakeMessage: Message object to be used on the reply to the message
        """
        data = data or {}
        return FakeMessage(msg_type, data, context=self.context)

    def reply(self, msg_type, data=None, context=None):
        """Construct a reply message for a given message

        This will take the same parameters as a message object but use
        the current message object as a reference.  It will copy the context
        from the existing message object and add any context passed in to
        the function.  Check for a destination passed in to the function from
        the data object and add that to the context as a destination.  If the
        context has a source then that will be swapped with the destination
        in the context.  The new message will then have data passed in plus the
        new context generated.

        Args:
            msg_type (str): type of message
            data (dict): data for message
            context: intended context for new message

        Returns:
            FakeMessage: Message object to be used on the reply to the message
        """
        data = deepcopy(data) or {}
        context = context or {}

        new_context = deepcopy(self.context)
        for key in context:
            new_context[key] = context[key]
        if 'destination' in data:
            new_context['destination'] = data['destination']
        if 'source' in new_context and 'destination' in new_context:
            s = new_context['destination']
            new_context['destination'] = new_context['source']
            new_context['source'] = s
        return FakeMessage(msg_type, data, context=new_context)

    def response(self, data=None, context=None):
        """Construct a response message for the message

        Constructs a reply with the data and appends the expected
        ".response" to the message

        Args:
            data (dict): message data
            context (dict): message context
        Returns
            (Message) message with the type modified to match default response
        """
        return self.reply(self.msg_type + '.response', data, context)

    def publish(self, msg_type, data, context=None):
        """
        Copy the original context and add passed in context.  Delete
        any target in the new context. Return a new message object with
        passed in data and new context.  Type remains unchanged.

        Args:
            msg_type (str): type of message
            data (dict): date to send with message
            context: context added to existing context

        Returns:
            FakeMessage: Message object to publish
        """
        context = context or {}
        new_context = self.context.copy()
        for key in context:
            new_context[key] = context[key]

        if 'target' in new_context:
            del new_context['target']

        return FakeMessage(msg_type, data, context=new_context)


class Message(FakeMessage):
    def __int__(self, *args, **kwargs):
        LOG.warning(f"This reference is deprecated, import from "
                    f"`ovos_bus_client.message` directly")
        FakeMessage.__init__(self, *args, **kwargs)


def get_message_lang(message=None):
    """Get the language from the message or the default language.
    Args:
        message: message to check for language code.
    Returns:
        The language code from the message or the default language.
    """
    try:
        from ovos_config.locale import get_default_lang
        default_lang = get_default_lang()
    except ImportError:
        LOG.warning("ovos_config not available. Using default lang en-us")
        default_lang = "en-us"
    message = message or dig_for_message()
    if not message:
        return default_lang
    lang = message.data.get("lang") or message.context.get("lang") or default_lang
    return lang.lower()


def get_websocket(host, port, route='/', ssl=False, threaded=True):
    """
    Returns a connection to a websocket
    """
    from ovos_bus_client import MessageBusClient

    client = MessageBusClient(host, port, route, ssl)
    if threaded:
        client.run_in_thread()
    return client


def get_mycroft_bus(host: str = None, port: int = None, route: str = None,
                    ssl: bool = None):
    """
    Returns a connection to the mycroft messagebus
    """
    try:
        from ovos_config.config import read_mycroft_config
        config = read_mycroft_config().get('websocket') or dict()
    except ImportError:
        LOG.warning("ovos_config not available. Falling back to default WS")
        config = dict()
    host = host or config.get('host') or _DEFAULT_WS_CONFIG['host']
    port = port or config.get('port') or _DEFAULT_WS_CONFIG['port']
    route = route or config.get('route') or _DEFAULT_WS_CONFIG['route']
    if ssl is None:
        ssl = config.get('ssl') if 'ssl' in config else \
            _DEFAULT_WS_CONFIG['ssl']
    return get_websocket(host, port, route, ssl)


def listen_for_message(msg_type, handler, bus=None):
    """
    Continuously listens and reacts to a specific messagetype on the mycroft messagebus

    NOTE: when finished you should call bus.remove(msg_type, handler)
    """
    bus = bus or get_mycroft_bus()
    bus.on(msg_type, handler)
    return bus


def listen_once_for_message(msg_type, handler, bus=None):
    """
    listens and reacts once to a specific messagetype on the mycroft messagebus
    """
    auto_close = bus is None
    bus = bus or get_mycroft_bus()

    def _handler(message):
        handler(message)
        if auto_close:
            bus.close()

    bus.once(msg_type, _handler)
    return bus


def wait_for_reply(message, reply_type=None, timeout=3.0, bus=None):
    """Send a message and wait for a response.

    Args:
        message (FakeMessage or str or dict): message object or type to send
        reply_type (str): the message type of the expected reply.
                          Defaults to "<message.type>.response".
        timeout: seconds to wait before timeout, defaults to 3
    Returns:
        The received message or None if the response timed out
    """
    auto_close = bus is None
    bus = bus or get_mycroft_bus()
    if isinstance(message, str):
        try:
            message = json.loads(message)
        except:
            pass
    if isinstance(message, str):
        message = FakeMessage(message)
    elif isinstance(message, dict):
        message = FakeMessage(message["type"],
                              message.get("data"),
                              message.get("context"))
    elif not isinstance(message, FakeMessage):
        raise ValueError
    response = bus.wait_for_response(message, reply_type, timeout)
    if auto_close:
        bus.close()
    return response


def send_message(message, data=None, context=None, bus=None):
    auto_close = bus is None
    bus = bus or get_mycroft_bus()
    if isinstance(message, str):
        if isinstance(data, dict) or isinstance(context, dict):
            message = FakeMessage(message, data, context)
        else:
            try:
                message = json.loads(message)
            except:
                message = FakeMessage(message)
    if isinstance(message, dict):
        message = FakeMessage(message["type"],
                              message.get("data"),
                              message.get("context"))
    if not isinstance(message, FakeMessage):
        raise ValueError
    bus.emit(message)
    if auto_close:
        bus.close()


def send_binary_data_message(binary_data, msg_type="mycroft.binary.data",
                             msg_data=None, msg_context=None, bus=None):
    msg_data = msg_data or {}
    msg = {
        "type": msg_type,
        "data": merge_dict(msg_data, {"binary": binary_data.hex()}),
        "context": msg_context or None
    }
    send_message(msg, bus=bus)


def send_binary_file_message(filepath, msg_type="mycroft.binary.file",
                             msg_context=None, bus=None):
    with open(filepath, 'rb') as f:
        binary_data = f.read()
    msg_data = {"path": filepath}
    send_binary_data_message(binary_data, msg_type=msg_type, msg_data=msg_data,
                             msg_context=msg_context, bus=bus)


def decode_binary_message(message):
    if isinstance(message, str):
        try:  # json string
            message = json.loads(message)
            binary_data = message.get("binary") or message["data"]["binary"]
        except:  # hex string
            binary_data = message
    elif isinstance(message, dict):
        # data field or serialized message
        binary_data = message.get("binary") or message["data"]["binary"]
    else:
        # message object
        binary_data = message.data["binary"]
    # decode hex string
    return bytearray.fromhex(binary_data)


def to_alnum(skill_id):
    """Convert a skill id to only alphanumeric characters

     Non alpha-numeric characters are converted to "_"

    Args:
        skill_id (str): identifier to be converted
    Returns:
        (str) String of letters
    """
    return ''.join(c if c.isalnum() else '_' for c in str(skill_id))


def unmunge_message(message, skill_id):
    """Restore message keywords by removing the Letterified skill ID.
    Args:
        message (FakeMessage): Intent result message
        skill_id (str): skill identifier
    Returns:
        Message without clear keywords
    """
    if hasattr(message, "data") and isinstance(message.data, dict):
        skill_id = to_alnum(skill_id)
        for key in list(message.data.keys()):
            if key.startswith(skill_id):
                # replace the munged key with the real one
                new_key = key[len(skill_id):]
                message.data[new_key] = message.data.pop(key)

    return message


def get_handler_name(handler):
    """Name (including class if available) of handler function.

    Args:
        handler (function): Function to be named

    Returns:
        string: handler name as string
    """
    if '__self__' in dir(handler) and 'name' in dir(handler.__self__):
        return handler.__self__.name + '.' + handler.__name__
    else:
        return handler.__name__


def create_wrapper(handler, skill_id, on_start, on_end, on_error):
    """Create the default skill handler wrapper.

    This wrapper handles things like metrics, reporting handler start/stop
    and errors.
        handler (callable): method/function to call
        skill_id: skill_id for associated skill
        on_start (function): function to call before executing the handler
        on_end (function): function to call after executing the handler
        on_error (function): function to call for error reporting
    """

    def wrapper(message):
        stopwatch = Stopwatch()
        try:
            message = unmunge_message(message, skill_id)
            if on_start:
                on_start(message)

            with stopwatch:
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

            # Send timing metrics
            context = message.context
            if context and 'ident' in context:
                try:
                    from mycroft.metrics import report_timing
                    report_timing(context['ident'], 'skill_handler', stopwatch,
                                  {'handler': handler.__name__,
                                   'skill_id': skill_id})
                except ImportError:
                    pass

    return wrapper


def create_basic_wrapper(handler, on_error=None):
    """Create the default skill handler wrapper.

    This wrapper handles things like metrics, reporting handler start/stop
    and errors.

    Args:
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
            if on_error:
                on_error(e)

    return wrapper


class EventContainer:
    """Container tracking messagbus handlers.

    This container tracks events added by a skill, allowing unregistering
    all events on shutdown.
    """

    def __init__(self, bus=None):
        self.bus = bus
        self.events = []

    def set_bus(self, bus):
        self.bus = bus

    def add(self, name, handler, once=False):
        """Create event handler for executing intent or other event.

        Args:
            name (string): IntentParser name
            handler (func): Method to call
            once (bool, optional): Event handler will be removed after it has
                                   been run once.
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

            LOG.debug('Added event: {}'.format(name))

    def remove(self, name):
        """Removes an event from bus emitter and events list.

        Args:
            name (string): Name of Intent or Scheduler Event
        Returns:
            bool: True if found and removed, False if not found
        """
        LOG.debug("Removing event {}".format(name))
        removed = False
        for _name, _handler in list(self.events):
            if name == _name:
                try:
                    self.events.remove((_name, _handler))
                except ValueError:
                    LOG.error('Failed to remove event {}'.format(name))
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
        """Unregister all registered handlers and clear the list of registered
        events.
        """
        for e, f in self.events:
            self.bus.remove(e, f)
        self.events = []  # Remove reference to wrappers


class BusService:
    """
    Provide some service over the messagebus for other components

    response = Message("face.recognition.reply")
    service = BusService(response)
    service.listen("face.recognition")

    while True:
        data = do_computation()
        service.update_response(data)  # replaces response.data

    """

    def __init__(self, message, trigger_messages=None, bus=None):
        self.bus = bus or get_mycroft_bus()
        self.response = message
        trigger_messages = trigger_messages or []
        self.events = []
        for message_type in trigger_messages:
            self.listen(message_type)

    def listen(self, message_type, callback=None):
        if callback is None:
            callback = self._respond
        self.bus.on(message_type, callback)
        self.events.append((message_type, callback))

    def update_response(self, data=None):
        if data is not None:
            self.response.data = data

    def _respond(self, message):
        self.bus.emit(message.reply(self.response.type, self.response.data))

    def shutdown(self):
        """ remove all listeners """
        for event, callback in self.events:
            self.bus.remove(event, callback)


class BusFeedProvider:
    """

    Meant to be subclassed


        class ClockService(BusFeedProvider):
            def __init__(self, name="clock_transmitter", bus=None):
                trigger_message  = Message("time.request")
                super().__init__(trigger_message, name, bus)
                self.set_data_gatherer(self.handle_get_time)

            def handle_get_time(self, message):
                self.update({"date": datetime.now()})


        clock_service = ClockService()

    """

    def __init__(self, trigger_message, name=None, bus=None, config=None):
        """
           initialize responder

           args:
                name(str): name identifier for .conf settings
                bus (WebsocketClient): mycroft messagebus websocket
        """
        if not config:
            LOG.warning(f"Expected a dict config and got None. This config"
                        f"fallback behavior will be deprecated in a future "
                        f"release")
            try:
                from ovos_config.config import read_mycroft_config
                config = read_mycroft_config()
            except ImportError:
                LOG.warning("ovos_config not available. Falling back to "
                            "default configuration")
                config = dict()
        self.trigger_message = trigger_message
        self.name = name or self.__class__.__name__
        self.bus = bus or get_mycroft_bus()
        self.callback = None
        self.service = None
        self._daemon = None
        self.config = config.get(self.name, {})

    def update(self, data):
        """
        change the data of the response to be sent when queried
        """
        if self.service is not None:
            self.service.update_response(data)

    def set_data_gatherer(self, callback, default_data=None, daemonic=False, interval=90):
        """
          prepare responder for sending, register answers
        """

        self.bus.remove_all_listeners(self.trigger_message)
        if ".request" in self.trigger_message:
            response_type = self.trigger_message.replace(".request", ".reply")
        else:
            response_type = self.trigger_message + ".reply"

        response = FakeMessage(response_type, default_data)
        self.service = BusService(response, bus=self.bus)
        self.callback = callback
        self.bus.on(self.trigger_message, self._respond)
        if daemonic:
            self._daemon = create_loop(self._data_daemon, interval)

    def _data_daemon(self):
        if self.callback is not None:
            self.callback(self.trigger_message)

    def _respond(self, message):
        """
          gather data and emit to bus
        """
        try:
            if self.callback:
                self.callback(message)
        except Exception as e:
            LOG.error(e)
        self.service.respond(message)

    def shutdown(self):
        self.bus.remove_all_listeners(self.trigger_message)
        if self._daemon:
            self._daemon.join(0)
            self._daemon = None
        if self.service:
            self.service.shutdown()
            self.service = None


class BusQuery:
    """
    retrieve data from some other component over the messagebus at any time

    message = Message("request.msg", {...}, {...})
    query = BusQuery(message)
    response = query.send()
    # do some more stuff
    response = query.send() # reutilize the object

    """

    def __init__(self, message, bus=None):
        self.bus = bus or get_mycroft_bus()
        self._waiting = False
        self.response = FakeMessage(None, None, None)
        self.query = message
        self.valid_response_types = []

    def add_response_type(self, response_type):
        """ listen to a new response_type """
        if response_type not in self.valid_response_types:
            self.valid_response_types.append(response_type)
            self.bus.on(response_type, self._end_wait)

    def _end_wait(self, message):
        self.response = message
        self._waiting = False

    def _wait_response(self, timeout):
        start = time.time()
        elapsed = 0
        self._waiting = True
        while self._waiting and elapsed < timeout:
            elapsed = time.time() - start
            time.sleep(0.1)
        self._waiting = False

    def send(self, response_type=None, timeout=10):
        self.response = FakeMessage(None, None, None)
        if response_type is None:
            response_type = self.query.type + ".reply"
        self.add_response_type(response_type)
        self.bus.emit(self.query)
        self._wait_response(timeout)
        return self.response

    def remove_listeners(self):
        for event in self.valid_response_types:
            self.bus.remove(event, self._end_wait)

    def shutdown(self):
        """ remove all listeners """
        self.remove_listeners()


class BusFeedConsumer:
    """
    this is meant to be subclassed

    class Clock(BusFeedConsumer):
        def __init__(self, name="clock_receiver", timeout=3, bus=None):
            request_message = Message("time.request")
            super().__init__(request_message, name, timeout, bus)

    # blocking
    clock = Clock()
    date = clock.request()["date"]

    # async
    clock = Clock(timeout=0) # non - blocking
    clock.request(daemonic=True, # loop on background
                  frequency=1) # update result every second

    date = clock.result["date"]

    """

    def __init__(self, query_message, name=None, timeout=5, bus=None,
                 config=None):
        self.query_message = query_message
        self.query_message.context["source"] = self.name
        self.name = name or self.__class__.__name__
        self.bus = bus or get_mycroft_bus()
        if not config:
            try:
                from ovos_config.config import read_mycroft_config
                config = read_mycroft_config()
            except ImportError:
                LOG.warning("Config not provided and ovos_config not available")
                config = dict()
        self.config = config.get(self.name, {})
        self.timeout = timeout
        self.query = None
        self.valid_responses = []
        self._daemon = None

    def request(self, response_messages=None, daemonic=False, interval=90):
        """
          prepare query for sending, add several possible kinds of
          response message automatically
                "message_type.reply" ,
                "message_type.response",
                "message_type.result"
        """
        response_messages = response_messages or []

        # generate valid reply message types
        self.valid_responses = response_messages
        if ".request" in self.query_message.type:
            response = self.query_message.type.replace(".request", ".reply")
            if response not in self.valid_responses:
                self.valid_responses.append(response)
            response = self.query_message.type.replace(".request", ".response")
            if response not in self.valid_responses:
                self.valid_responses.append(response)
            response = self.query_message.type.replace(".request", ".result")
            if response not in self.valid_responses:
                self.valid_responses.append(response)
        else:
            response = self.query_message.type + ".reply"
            if response not in self.valid_responses:
                self.valid_responses.append(response)
            response = self.query_message.type + ".response"
            if response not in self.valid_responses:
                self.valid_responses.append(response)
            response = self.query_message.type + ".result"
            if response not in self.valid_responses:
                self.valid_responses.append(response)

        # update message context
        self.query_message.context["valid_responses"] = self.valid_responses

        self._query()
        if daemonic:
            self._daemon = create_loop(self._request_daemon, interval)
        return self.result

    def _request_daemon(self):
        self.query.send(self.valid_responses[0], self.timeout)

    def _query(self):
        self.query = BusQuery(self.query_message)
        for message in self.valid_responses[1:]:
            self.query.add_response_type(message)
        self.query.send(self.valid_responses[0], self.timeout)

    @property
    def result(self):
        return self.query.response.data

    def shutdown(self):
        """ remove all listeners """
        if self._daemon:
            self._daemon.join(0)
            self._daemon = None
        if self.query:
            self.query.shutdown()
