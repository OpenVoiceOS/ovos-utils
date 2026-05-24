import asyncio
import warnings
from threading import Event

from ovos_utils.log import LOG, log_deprecation
from pyee import EventEmitter


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
        except Exception:
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
        try:
            self.ee.emit(message.msg_type, message)
        except Exception as e:
            LOG.exception(f"Error in event handler for '{message.msg_type}': {e}")
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
        parsed_message = FakeMessage.deserialize(message)
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
        except Exception:
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


# The reference Message envelope lives in ovos-spec-tools (OVOS-MSG-1).
# ovos-utils re-exports it under the historical ``FakeMessage`` name and
# attaches the one legacy convenience method downstream still uses —
# ``publish`` — to the class at import time. ``as_dict`` is now on the
# spec-tools class itself; the ``data['destination']`` promotion the
# old ``reply`` did was always a bug (data is the payload, context owns
# routing) and is gone.
#
# The old ``_MutableMessage`` metaclass / dynamic ``__new__`` indirection
# (which tried to return an ``ovos_bus_client.Message`` at runtime if
# bus-client was installed) is no longer needed: spec-tools is a hard
# dependency, the canonical class is always present, and
# ``ovos-bus-client.Message`` is the **same** class (bus-client attaches
# ``publish`` to it too — both attachments are idempotent).
from typing import Any, Dict, Optional

from ovos_spec_tools.message import Message as FakeMessage


def _publish(self, msg_type: str, data: Dict[str, Any],
             context: Optional[Dict[str, Any]] = None) -> FakeMessage:
    """Relay under a new topic without the §5.2 swap; drop ``target``."""
    context = context or {}
    new_context = dict(self.context)
    new_context.update(context)
    new_context.pop("target", None)
    return self.__class__(msg_type, data, new_context)


# Attach publish() to the spec-tools Message so the method appears on
# every Message instance regardless of which package the caller imported
# the class from. Idempotent with ovos-bus-client's identical attachment.
FakeMessage.publish = _publish


class Message(FakeMessage):
    """Deprecated alias for the OVOS-MSG-1 ``Message`` envelope.

    ``from ovos_utils.fakebus import Message`` is in the wild and stays
    importable through one more release. New code should import the
    envelope where it lives — :class:`ovos_spec_tools.Message` (or
    :class:`ovos_bus_client.Message`, which is a subclass).
    """

    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "ovos_utils.fakebus.Message is deprecated; import "
            "ovos_spec_tools.Message (or ovos_bus_client.Message)",
            DeprecationWarning,
            stacklevel=2,
        )
        log_deprecation(
            "please import Message from ovos_spec_tools / "
            "ovos_bus_client directly", "1.0.0")
        return FakeMessage(*args, **kwargs)


class AsyncFakeBus:
    """In-process stand-in for ``AsyncMessageBusClient``.

    Mirrors the same surface as the real async bus client: ``connect`` /
    ``close`` / ``emit`` / ``wait_for_message`` / ``wait_for_response`` are
    coroutines; ``on`` / ``once`` / ``remove`` stay synchronous.

    No WebSocket, no thread, no real I/O — every emit dispatches
    synchronously through a ``pyee.EventEmitter`` to whatever handlers
    are registered.

    Useful both in tests (drop-in for ``AsyncMessageBusClient``) and at
    runtime (anywhere a sync component expects the legacy ``FakeBus`` but
    the surrounding code is asyncio-native).

    The session-injection side effects match ``FakeBus`` so multi-turn
    flows behave identically.
    """

    def __init__(self, *args, **kwargs):
        self.started_running = False
        self.session_id = "default"
        self.ee = kwargs.get("emitter") or EventEmitter()
        self.ee.on("error", self.on_error)
        self.connected_event = asyncio.Event()
        self.connected_event.set()
        self.on_open()
        try:
            self.session_id = kwargs["session"].session_id
        except Exception:
            pass  # don't care

        self.on("ovos.session.update_default",
                self.on_default_session_update)

    # ------------------------------------------------------------------
    # Handler registration (sync — matches AsyncMessageBusClient)
    # ------------------------------------------------------------------

    def on(self, msg_type, handler):
        self.ee.on(msg_type, handler)

    def once(self, msg_type, handler):
        self.ee.once(msg_type, handler)

    def remove(self, msg_type, handler):
        try:
            self.ee.remove_listener(msg_type, handler)
        except Exception:
            pass

    def remove_all_listeners(self, event_name):
        self.ee.remove_all_listeners(event_name)

    # ------------------------------------------------------------------
    # Lifecycle (async)
    # ------------------------------------------------------------------

    async def connect(self, *args, **kwargs):
        """No-op for the fake bus; matches the real client's lifecycle.

        Returns immediately with ``connected_event`` set.
        """
        self.started_running = True
        self.connected_event.set()
        return self

    async def close(self):
        self.connected_event.clear()
        self.on_close()

    # ------------------------------------------------------------------
    # emit (async) — same dispatch shape as FakeBus.emit
    # ------------------------------------------------------------------

    async def emit(self, message):
        if "session" not in message.context:
            try:  # replicate side effects
                from ovos_bus_client.session import Session, SessionManager
                sess = SessionManager.sessions.get(self.session_id) or \
                       Session(self.session_id)
                message.context["session"] = sess.serialize()
            except ImportError:  # don't care
                message.context["session"] = {"session_id": self.session_id}
        self.ee.emit("message", message.serialize())
        try:
            self.ee.emit(message.msg_type, message)
        except Exception as e:
            LOG.exception(f"Error in event handler for '{message.msg_type}': {e}")
        self.on_message(message.serialize())

    # ------------------------------------------------------------------
    # Sync helpers used internally — same as FakeBus
    # ------------------------------------------------------------------

    def on_message(self, *args):
        """Handle an incoming websocket message.

        @param args:
            message (str): serialized Message
        """
        if len(args) == 1:
            message = args[0]
        else:
            message = args[1]
        parsed_message = FakeMessage.deserialize(message)
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

    def on_error(self, error):
        LOG.error(error)

    def on_open(self):
        pass

    def on_close(self):
        pass

    # ------------------------------------------------------------------
    # Waiters (async)
    # ------------------------------------------------------------------

    async def wait_for_message(self, message_type, timeout=3.0):
        """Wait for a message of a specific type.

        Arguments:
            message_type (str): the message type of the expected message
            timeout: seconds to wait before timeout, defaults to 3

        Returns:
            The received message or None if the response timed out
        """
        evt = asyncio.Event()
        captured = {"msg": None}

        def _rcv(m):
            captured["msg"] = m
            evt.set()

        self.ee.once(message_type, _rcv)
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        return captured["msg"]

    async def wait_for_response(self, message, reply_type=None, timeout=3.0):
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
        evt = asyncio.Event()
        captured = {"msg": None}

        def _rcv(m):
            captured["msg"] = m
            evt.set()

        self.ee.once(reply_type, _rcv)
        await self.emit(message)
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        return captured["msg"]

    # ------------------------------------------------------------------
    # Backwards-compat passthroughs so AsyncFakeBus is a drop-in even for
    # code paths that still call the threading-era helpers.
    # ------------------------------------------------------------------

    def create_client(self):
        return self

    def run_forever(self):
        self.started_running = True

    def run_in_thread(self):
        self.run_forever()
