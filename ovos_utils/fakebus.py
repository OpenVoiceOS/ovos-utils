import asyncio
import warnings
from os import environ
from threading import Event

from ovos_utils.log import LOG, log_deprecation
from ovos_spec_tools import NamespaceTranslator
from pyee import EventEmitter


def dig_for_message():
    try:
        from ovos_bus_client.message import dig_for_message as _dig
        return _dig()
    except ImportError:
        pass
    return None


# sentinel: lets us tell "kwarg not passed" apart from "kwarg passed True/False"
_UNSET = object()


def _bus_flag(env_var, config_key, default=True):
    """Resolve a boolean bus flag the way ``MessageBusClient._bus_flag`` does.

    Precedence: env var (when set) > ``websocket.<config_key>`` in ovos_config
    > ``default``. The env var wins when set to a truthy/falsy string; ovos_config
    is optional, so any failure to read it falls back to ``default``.

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


def _resolve_bus_flags(kwargs):
    """Build the namespace ``NamespaceTranslator`` for a fake bus instance.

    An explicitly-passed ``modernize``/``emit_legacy`` kwarg wins (back-compat for
    callers passing ``emit_legacy=True/False``); otherwise the flag is resolved via
    env var -> ``websocket.*`` config -> default ``True``, matching the real client.
    """
    modernize = kwargs.get("modernize", _UNSET)
    if modernize is _UNSET:
        modernize = _bus_flag("OVOS_BUS_MODERNIZE", "modernize", default=True)
    emit_legacy = kwargs.get("emit_legacy", _UNSET)
    if emit_legacy is _UNSET:
        emit_legacy = _bus_flag("OVOS_BUS_EMIT_LEGACY", "emit_legacy", default=True)
    return NamespaceTranslator(modernize=modernize, emit_legacy=emit_legacy)


# --- legacy intent-topic compat (non-normative migration tooling) ----------
#
# Old ovos-workshop releases built the per-intent dispatch topic from the
# padatious resource FILENAME, so the ``.intent`` extension leaked onto the
# wire: a skill with ``food.order.intent`` listened on
# ``<skill_id>:food.order.intent``. Current workshop is spec-pure and
# registers the canonical ``<skill_id>:food.order`` (OVOS-MSG-1 §2.1.1).
from ovos_spec_tools.intent_topics import (canonical_intent_topic,
                                           is_intent_topic,
                                           legacy_intent_topic)

#: Context flag stamped on a twin intent frame. Same key and same meaning as
#: in ``ovos_bus_client.client.client``.
INTENT_COMPAT_TWIN_KEY = "_intent_compat_twin"


class _LegacyIntentBridge:
    """Bridge the canonical and legacy spellings of an intent dispatch topic.

    Shared by :class:`FakeBus` and :class:`AsyncFakeBus` so both test doubles
    behave like ``ovos_bus_client.MessageBusClient``, which runs the same
    bridge next to its namespace bridge. A test double that skipped it would
    hide the compat path from every harness built on it.

    The real client splits the bridge over a wire send and a wire receive. A
    fake bus is one process, so both rules land in ``emit``:

    * a CANONICAL dispatch also fires its ``.intent``-suffixed twin, marked as
      a twin, reaching a handler written against old workshop;
    * a SUFFIXED dispatch that is NOT already such a twin also fires its
      canonical spelling, reaching a spec-pure handler.

    The two cases are mutually exclusive and neither cascades, so one emit
    reaches each handler exactly once. Nothing tracks who listens to what.
    """

    def _bridge_intent_topics(self, message):
        """Fire the counterpart spelling of an intent dispatch, if any."""
        if not self._translator.emit_legacy:
            return
        if not is_intent_topic(message.msg_type):
            return
        canonical = canonical_intent_topic(message.msg_type)
        if canonical == message.msg_type:
            twin = message.forward(legacy_intent_topic(message.msg_type),
                                   message.data)
            twin.context[INTENT_COMPAT_TWIN_KEY] = True
            self.ee.emit(twin.msg_type, twin)
        elif not message.context.get(INTENT_COMPAT_TWIN_KEY):
            self.ee.emit(canonical, message.forward(canonical, message.data))


class FakeBus(_LegacyIntentBridge):
    def __init__(self, *args, **kwargs):
        self.started_running = False
        self.session_id = "default"
        self.ee = kwargs.get("emitter") or EventEmitter()
        self.ee.on("error", self.on_error)
        # mirror MessageBusClient's namespace migration so the test/satellite
        # double bridges legacy<->ovos.* topics identically. Flags resolve the
        # same way the real client does: explicit modernize=/emit_legacy= kwarg
        # wins, else env var -> websocket.* config -> default on.
        self._translator = _resolve_bus_flags(kwargs)
        self._handler_guards = {}        # handler -> shared mirror-guard
        self._dedup_registrations = {}   # handler -> [(msg_type, wrapped), ...]
        self.on_open()
        try:
            self.session_id = kwargs["session"].session_id
        except Exception:
            pass  # don't care

        self.on("ovos.session.update_default",
                self.on_default_session_update)

    def on(self, msg_type, handler):
        # wrap handlers on migrated topics so a handler subscribed to both the
        # legacy and ovos.* topic fires once (the mirror is dropped)
        if self._translator.is_migrated(msg_type):
            guard = self._handler_guards.get(handler)
            if guard is None:
                guard = self._translator.new_mirror_guard()
                self._handler_guards[handler] = guard

            def wrapped(message=None):
                if guard(message):
                    return
                return handler(message)

            self.ee.on(msg_type, wrapped)
            self._dedup_registrations.setdefault(handler, []).append((msg_type, wrapped))
            return
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
        # namespace migration: also dispatch the counterpart topic(s) so a
        # listener on either namespace receives the event (consumers dedupe).
        # the mirrored payload is reshaped into the counterpart topic's shape
        # (identity for payload-compatible renames, a per-topic transform for
        # shape-changing ones) so a listener on it receives the payload in *its*
        # shape -- matching MessageBusClient's bridge.
        for topic in self._translator.counterpart_topics(message.msg_type):
            try:
                translated = self._translator.translate_payload(
                    from_topic=message.msg_type, to_topic=topic,
                    data=message.data)
                self.ee.emit(topic, message.forward(topic, translated))
            except Exception as e:
                LOG.exception(f"Error in counterpart dispatch for '{topic}': {e}")
        # legacy intent-topic bridge: fire the counterpart spelling of an
        # intent dispatch, for handlers written against old workshop.
        self._bridge_intent_topics(message)

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
        regs = self._dedup_registrations.get(handler)
        if regs:
            for ev, wrapped in [r for r in regs if r[0] == msg_type]:
                try:
                    self.ee.remove_listener(ev, wrapped)
                except Exception:
                    pass
                regs.remove((ev, wrapped))
            if not regs:
                self._dedup_registrations.pop(handler, None)
                self._handler_guards.pop(handler, None)
            return
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


class AsyncFakeBus(_LegacyIntentBridge):
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
        # mirror MessageBusClient's namespace migration (see FakeBus.__init__).
        self._translator = _resolve_bus_flags(kwargs)
        self._handler_guards = {}        # handler -> shared mirror-guard
        self._dedup_registrations = {}   # handler -> [(msg_type, wrapped), ...]
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
        # wrap handlers on migrated topics so a handler subscribed to both the
        # legacy and ovos.* topic fires once (the mirror is dropped) -- same as
        # FakeBus.on / MessageBusClient.on.
        if self._translator.is_migrated(msg_type):
            guard = self._handler_guards.get(handler)
            if guard is None:
                guard = self._translator.new_mirror_guard()
                self._handler_guards[handler] = guard

            def wrapped(message=None):
                if guard(message):
                    return
                return handler(message)

            self.ee.on(msg_type, wrapped)
            self._dedup_registrations.setdefault(handler, []).append((msg_type, wrapped))
            return
        self.ee.on(msg_type, handler)

    def once(self, msg_type, handler):
        self.ee.once(msg_type, handler)

    def remove(self, msg_type, handler):
        regs = self._dedup_registrations.get(handler)
        if regs:
            for ev, wrapped in [r for r in regs if r[0] == msg_type]:
                try:
                    self.ee.remove_listener(ev, wrapped)
                except Exception:
                    pass
                regs.remove((ev, wrapped))
            if not regs:
                self._dedup_registrations.pop(handler, None)
                self._handler_guards.pop(handler, None)
            return
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
        # namespace migration: also dispatch the counterpart topic(s) with the
        # payload reshaped into each counterpart's shape -- same as FakeBus.emit.
        for topic in self._translator.counterpart_topics(message.msg_type):
            try:
                translated = self._translator.translate_payload(
                    from_topic=message.msg_type, to_topic=topic,
                    data=message.data)
                self.ee.emit(topic, message.forward(topic, translated))
            except Exception as e:
                LOG.exception(f"Error in counterpart dispatch for '{topic}': {e}")
        # legacy intent-topic bridge: fire the counterpart spelling of an
        # intent dispatch, for handlers written against old workshop.
        self._bridge_intent_topics(message)

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
