from mycroft_bus_client import MessageBusClient, Message
from ovos_utils.log import LOG
from ovos_utils.configuration import read_mycroft_config
from ovos_utils import create_loop
from ovos_utils.json_helper import merge_dict
import time
import json
from pyee import BaseEventEmitter
from threading import Event


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


def get_websocket(host, port, route='/', ssl=False, threaded=True):
    """
    Returns a connection to a websocket
    """
    client = MessageBusClient(host, port, route, ssl)
    if threaded:
        client.run_in_thread()
    return client


def get_mycroft_bus(host='0.0.0.0', port=8181, route='/core', ssl=False):
    """
    Returns a connection to the mycroft messagebus
    """
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
        message (Message or str or dict): message object or type to send
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
        message = Message(message)
    elif isinstance(message, dict):
        message = Message(message["type"],
                          message.get("data"),
                          message.get("context"))
    elif not isinstance(message, Message):
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
            message = Message(message, data, context)
        else:
            try:
                message = json.loads(message)
            except:
                message = Message(message)
    if isinstance(message, dict):
        message = Message(message["type"],
                          message.get("data"),
                          message.get("context"))
    if not isinstance(message, Message):
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
        config = config or read_mycroft_config()
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

        response = Message(response_type, default_data)
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
        self.response = Message(None, None, None)
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
        self.response = Message(None, None, None)
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
        config = config or read_mycroft_config()
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
