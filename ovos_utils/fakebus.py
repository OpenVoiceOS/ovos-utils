import asyncio
import warnings
from os import environ
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


def _bus_flag(env_var, config_key, default=False):
    """Resolve a boolean bus flag the way ``MessageBusClient._bus_flag`` does.

    Precedence: env var (when set) > ``websocket.<config_key>`` in ovos_config
    > ``default``.

    Kept layering-clean: mirrors ``ovos_bus_client.client.client._bus_flag``
    without importing from bus-client (bus-client depends on utils, not vice-versa).
    """
    val = environ.get(env_var)
    if val is not None:
        return val.strip().lower() in ("1", "true", "yes", "on")
    try:
        from ovos_config import Configuration
        return bool(Configuration().get("websocket", {}).get(config_key, default))
    except Exception:
        return default


# --- the legacy wire bridge is GONE -----------------------------------------
#
# The fake bus used to mirror ``MessageBusClient``'s two migration bridges: the
# OVOS-MSG-1 namespace bridge (a spec topic also reached listeners on the
# legacy topic it replaced, and the reverse) and the OVOS-INTENT-4 intent-topic
# bridge (a canonical ``<skill_id>:<intent>`` dispatch also reached the old
# ``<skill_id>:<intent>.intent`` spelling). Both were removed from the real
# client, so both are removed here — a test double that kept them would let a
# harness pass against behaviour the fleet no longer has.

#: Bus flags that used to steer the bridge.
_REMOVED_BRIDGE_FLAGS = (
    ("OVOS_BUS_EMIT_LEGACY", "emit_legacy"),
    ("OVOS_BUS_MODERNIZE", "modernize"),
    ("OVOS_BUS_INTENT_REEMIT_BLANKET", "intent_reemit_blanket"),
)


def _reject_removed_bridge_flags(kwargs):
    """Handle a caller that still asks for the removed bridge.

    The two spellings get different treatment on purpose.

    An **env var or config entry** is an operator asking a live deployment to
    keep the legacy topics on the wire. That belief is now wrong, and silence
    would hand them a fleet that drops messages, so it raises — the same error
    the real ``MessageBusClient`` raises.

    A **constructor kwarg** is a test harness, not a deployment. Harnesses
    across the ecosystem pass ``emit_legacy=True`` unconditionally (ovoscope's
    ``MiniCroft`` is one), and raising there would break every one of them at
    construction without telling anybody anything useful. The kwarg is
    accepted, ignored, and warned about instead.
    """
    for env_var, config_key in _REMOVED_BRIDGE_FLAGS:
        if _bus_flag(env_var, config_key, default=False):
            raise RuntimeError(
                f"'{config_key}' (env {env_var}) is enabled, but the legacy "
                "wire bridge was removed from the fake bus, matching "
                "ovos-bus-client. Legacy bus topics are no longer emitted or "
                "mirrored. Migrate the producers and consumers to the "
                f"OVOS-MSG-1 spec topics, then unset '{config_key}'.")
        if kwargs.get(config_key):
            log_deprecation(
                f"the '{config_key}' kwarg no longer does anything: the "
                "legacy wire bridge was removed from the fake bus. Drop it "
                "from the call.", "1.0.0")


class FakeBus:
    def __init__(self, *args, **kwargs):
        self.started_running = False
        self.session_id = "default"
        self.ee = kwargs.get("emitter") or EventEmitter()
        self.ee.on("error", self.on_error)
        # the migration window is over: no namespace bridge, no intent-topic
        # twin, no mirror-guard — matching MessageBusClient.
        _reject_removed_bridge_flags(kwargs)
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
        # Fold the incoming message's session onto the SessionManager singleton
        # BEFORE running handlers, matching the real MessageBusClient.on_message
        # order (receive -> fold -> dispatch to handlers). Folding AFTER handlers
        # would wipe any in-place / synced session mutation the handlers made
        # (handle_session_sync merging intent_context, handle_add_context injecting
        # context frames, ...), because the message's session snapshot was
        # stamped at emit-time, before those mutations landed — a spec-violating
        # self-broadcast-back wipe. The single-process harness has no separate
        # receiver, so it must not re-fold its own emit once the handlers have
        # run.
        self.on_message(message.serialize())
        self.ee.emit("message", message.serialize())
        try:
            self.ee.emit(message.msg_type, message)
        except Exception as e:
            LOG.exception(f"Error in event handler for '{message.msg_type}': {e}")

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
            # every session — including the default id — folds onto the singleton
            # (value-passing; nothing is owner-only, matching the spec-tools
            # SessionManager and the real MessageBusClient)
            SessionManager.update(sess)
        except ImportError:
            pass  # don't care

    def on_default_session_update(self, message):
        try:  # replicate side effects
            from ovos_bus_client.session import Session, SessionManager
            new_session = message.data["session_data"]
            sess = Session.deserialize(new_session)
            # payload is default_session.serialize() (id == "default"); the
            # SessionManager singleton syncs default_session by id, so the
            # deprecated make_default flag is not needed.
            SessionManager.update(sess)
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
from ovos_utils.log import deprecated
from ovos_utils.version import VERSION_MAJOR


# OVOS-MSG-1 defines forward / reply / response as the three normative
# derivations (§5). ``publish`` is a bus-client tradition outside the
# spec; it survives as an attached method for one more major release so
# downstream consumers can migrate.
_PUBLISH_REMOVAL_VERSION = f"{VERSION_MAJOR + 1}.0.0"


@deprecated(
    "Message.publish is deprecated; use Message.forward (relay under a "
    "new topic, preserves context) or Message.reply (§5.2 swap) — both "
    "are OVOS-MSG-1 normative",
    _PUBLISH_REMOVAL_VERSION)
def _publish(self, msg_type: str, data: Dict[str, Any],
             context: Optional[Dict[str, Any]] = None) -> FakeMessage:
    """Relay under a new topic without the §5.2 swap; drop ``target``.

    .. deprecated::
        Not part of OVOS-MSG-1 (the spec defines ``forward`` /
        ``reply`` / ``response`` as the only normative derivations).
        Slated for removal in the next major; use :meth:`forward`
        when you do not want the routing-key swap, or :meth:`reply`
        when you do.
    """
    import warnings
    # stacklevel=3: warn() -> body -> @deprecated wrapper -> caller
    warnings.warn(
        "Message.publish is deprecated; use Message.forward (no §5.2 "
        "swap) or Message.reply (with swap) instead — both are "
        "OVOS-MSG-1 normative derivations. ``publish`` will be removed "
        f"in ovos-utils {_PUBLISH_REMOVAL_VERSION}.",
        DeprecationWarning, stacklevel=3)
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


class AsyncFakeBus():
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
        # no legacy wire bridge (see FakeBus.__init__).
        _reject_removed_bridge_flags(kwargs)
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
        # Fold BEFORE handlers — see FakeBus.emit for the rationale (a post-
        # handler self-broadcast-back fold wipes the handlers' in-place / synced
        # session mutations with the stale emit-time snapshot).
        self.on_message(message.serialize())
        self.ee.emit("message", message.serialize())
        try:
            self.ee.emit(message.msg_type, message)
        except Exception as e:
            LOG.exception(f"Error in event handler for '{message.msg_type}': {e}")

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
            # every session — including the default id — folds onto the singleton
            # (value-passing; nothing is owner-only, matching the spec-tools
            # SessionManager and the real MessageBusClient)
            SessionManager.update(sess)
        except ImportError:
            pass  # don't care

    def on_default_session_update(self, message):
        try:  # replicate side effects
            from ovos_bus_client.session import Session, SessionManager
            new_session = message.data["session_data"]
            sess = Session.deserialize(new_session)
            # payload is default_session.serialize() (id == "default"); the
            # SessionManager singleton syncs default_session by id, so the
            # deprecated make_default flag is not needed.
            SessionManager.update(sess)
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
