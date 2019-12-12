from jarbas_utils.log import LOG

try:
    from mycroft_bus_client import MessageBusClient, Message
except ImportError:
    # TODO add to setup.py blocked until https://github.com/MycroftAI/mycroft-messagebus-client is on pip
    # TODO create websocket connection manually or just wait?
    MessageBusClient = None


    class Message(dict):
        @property
        def type(self):
            return self.get("type", "mycroft_message")

        @property
        def data(self):
            return self.get("data", {})

        @property
        def context(self):
            return self.get("context", {})


def get_mycroft_bus():
    """
    TODO add host to params
    Returns a connection to the mycroft messagebus
    """
    if MessageBusClient is None:
        LOG.error("pip install git+https://github.com/MycroftAI/mycroft-messagebus-client")
        raise ImportError("mycroft-messagebus-client not found")
    client = MessageBusClient()
    client.run_in_thread()
    return client


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
    bus = bus or get_mycroft_bus()
    bus.once(msg_type, handler)
    return bus


def wait_for_reply(message, reply_type=None, timeout=None, bus=None):
    """Send a message and wait for a response.

    Args:
        message (Message or str or dict): message object or type to send
        reply_type (str): the message type of the expected reply.
                          Defaults to "<message.type>.response".
        timeout: seconds to wait before timeout, defaults to 3
    Returns:
        The received message or None if the response timed out
    """
    bus = bus or get_mycroft_bus()
    if isinstance(message, str):
        # TODO check for json
        message = Message(message)
    elif isinstance(message, dict):
        message = Message(message["type"],
                          message.get("data"),
                          message.get("context"))
    elif not isinstance(message, Message):
        raise ValueError
    return bus.wait_for_response(message, reply_type, timeout)
