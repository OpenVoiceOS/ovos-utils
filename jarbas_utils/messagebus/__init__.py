from mycroft_bus_client import MessageBusClient, Message
import json


def get_websocket(host, port, route='/', ssl=False):
    """
    Returns a connection to a websocket
    """
    client = MessageBusClient(host, port, route, ssl)
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
