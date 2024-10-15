import json
from copy import deepcopy
from threading import Event

from pyee import EventEmitter

from ovos_utils.log import LOG, log_deprecation


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
        self.session_id = "default"
        self.ee = kwargs.get("emitter") or EventEmitter()
        self.ee.on("error", self.on_error)
        self.on_open()
        try:
            self.session_id = kwargs["session"].session_id
        except:
            pass  # don't care

        self.on("ovos.session.update_default",
                self.on_default_session_update)

    def on(self, msg_type, handler):
        self.ee.on(msg_type, handler)

    def once(self, msg_type, handler):
        self.ee.once(msg_type, handler)

    def emit(self, message):
        if "session" not in message.context:
            try:  # replicate side effects
                from ovos_bus_client.session import Session, SessionManager
                sess = SessionManager.sessions.get(self.session_id) or \
                       Session(self.session_id)
                message.context["session"] = sess.serialize()
            except ImportError:  # don't care
                message.context["session"] = {"session_id": self.session_id}
        self.ee.emit("message", message.serialize())
        self.ee.emit(message.msg_type, message)
        self.on_message(message.serialize())

    def on_message(self, *args):
        """
        Handle an incoming websocket message
        @param args:
            message (str): serialized Message
        """
        if len(args) == 1:
            message = args[0]
        else:
            message = args[1]
        parsed_message = Message.deserialize(message)
        try:  # replicate side effects
            from ovos_bus_client.session import Session, SessionManager
            sess = Session.from_message(parsed_message)
            if sess.session_id != "default":
                # 'default' can only be updated by core
                SessionManager.update(sess)
        except ImportError:
            pass  # don't care

    def on_default_session_update(self, message):
        try:  # replicate side effects
            from ovos_bus_client.session import Session, SessionManager
            new_session = message.data["session_data"]
            sess = Session.deserialize(new_session)
            SessionManager.update(sess, make_default=True)
            LOG.debug("synced default_session")
        except ImportError:
            pass  # don't care

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
        except ImportError:
            pass
        try:
            from mycroft_bus_client.message import Message as _MycroftMessage
            if isinstance(instance, _MycroftMessage):
                return True
        except ImportError:
            pass
        return super().__instancecheck__(instance)


# fake Message object to allow usage without ovos-bus-client installed
class FakeMessage(metaclass=_MutableMessage):
    """ fake Message object to allow usage with FakeBus without ovos-bus-client installed"""

    def __new__(cls, *args, **kwargs):
        try:  # most common case
            from ovos_bus_client import Message as _M
            return _M(*args, **kwargs)
        except ImportError:
            pass
        try:  # some old install that upgraded during migration period
            from mycroft_bus_client import Message as _M
            return _M(*args, **kwargs)
        except ImportError:  # FakeMessage
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
        log_deprecation(f"Import from ovos_bus_client.message directly",
                        "0.1.0")
        FakeMessage.__init__(self, *args, **kwargs)
