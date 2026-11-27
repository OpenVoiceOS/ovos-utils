# FakeBus
<!-- agent-hint
covers: how to test bus code without a messagebus, with FakeBus and AsyncFakeBus
source: ovos_utils/fakebus.py
generated: no
verify: python3 docs/check_page.py docs/fakebus.md
see: events.md
-->

**Module:** `ovos_utils.fakebus`

In-process message bus and message implementation for testing, standalone usage, or environments where `ovos-bus-client` is not available. Behaves like the real `MessageBusClient` API without any WebSocket connection.

---

## `FakeBus`

```python
from ovos_utils.fakebus import FakeBus, FakeMessage

bus = FakeBus()

def on_utterance(message):
    print(message.data["utterances"])

bus.on("recognizer_loop:utterance", on_utterance)
bus.emit(FakeMessage("recognizer_loop:utterance", {"utterances": ["hello"]}))
```

### Internals

`FakeBus` uses a `pyee.EventEmitter` internally. When `emit()` is called:

1. Injects `session` into `message.context` if not present (replicates the real bus side effect)
2. Emits `"message"` with the serialized payload on the emitter
3. Emits `message.msg_type` directly on the emitter (for `bus.on()` handlers)
4. Calls `on_message()` with the serialized payload

### Topic bridges

`FakeBus` and `AsyncFakeBus` copy two bridges of `MessageBusClient`, so a test sees the same delivery as on a real bus:

- **Namespace bridge.** An emit on either spelling of a migrated topic (legacy or `ovos.*`) also dispatches the other spelling. When the migration changed the payload, the copy has the shape of the other spelling. `ovos_spec_tools.NamespaceTranslator` gives the topic pairs.
- **Intent-topic bridge.** An emit on an intent topic also dispatches its counterpart with or without the `.intent` suffix.

Know these limits before you write a test:

- A `FakeBus` is one bus connection. The two spellings of an intent topic share one guard. When both spellings have listeners, only the spelling that was emitted, or its canonical form, is delivered. A listener on the legacy spelling only gets nothing from a canonical emit.
- The copy that a bridge dispatches does not fire the `"message"` listener a second time. On a real bus the copy is a second frame. A test that listens on `"message"` sees one capture for each emit. Listen on the canonical topic when the copy matters.
- A `FakeBus` cannot model two connections. An observer on the same `FakeBus` shares the guard of the code under test.

### Session Handling

`FakeBus` replicates `SessionManager` side effects from `ovos-bus-client` if that package is installed:
- `emit()` serializes the current session into `message.context["session"]`
- `on_message()` calls `Session.from_message()` and `SessionManager.update()`
- `on_default_session_update()` updates the default session when `ovos.session.update_default` is received

### Key Methods

| Method | Description |
|---|---|
| `on(msg_type, handler)` | Register a handler for a message type |
| `once(msg_type, handler)` | Register a one-time handler |
| `emit(message)` | Dispatch a message locally |
| `remove(msg_type, handler)` | Unregister a handler |
| `remove_all_listeners(event_name)` | Remove all handlers for a message type |
| `wait_for_message(message_type, timeout)` | Block until a message of that type arrives |
| `wait_for_response(message, reply_type, timeout)` | Emit a message and wait for its response |
| `run_forever()` | No-op (sets `started_running = True`) |
| `run_in_thread()` | Calls `run_forever()` |
| `close()` | Calls `on_close()` |
| `create_client()` | Returns `self` |

For asyncio-native code, see [`AsyncFakeBus`](#asyncfakebus) below.

---

## `AsyncFakeBus`

`AsyncFakeBus` in `ovos_utils/fakebus.py`

In-process stand-in for `AsyncMessageBusClient` (from `ovos-bus-client`). Use this when your code is asyncio-native and needs a drop-in fake bus without a WebSocket connection. The API surface mirrors the real async client: coroutine methods keep you inside the event loop, while handler registration stays synchronous to match `pyee` and the real client's contract.

```python
import asyncio
from ovos_utils.fakebus import AsyncFakeBus, FakeMessage

async def main():
    bus = AsyncFakeBus()

    received = []

    def on_ping(message):
        received.append(message)

    bus.on("test:ping", on_ping)

    await bus.emit(FakeMessage("test:ping", {"n": 1}))
    print(received)  # [FakeMessage("test:ping", ...)]

    await bus.close()

asyncio.run(main())
```

### Coroutine vs sync split

| Sync (handler registration) | Async (I/O surface) |
|---|---|
| `on(msg_type, handler)` | `connect(*args, **kwargs)` |
| `once(msg_type, handler)` | `close()` |
| `remove(msg_type, handler)` | `emit(message)` |
| `remove_all_listeners(event_name)` | `wait_for_message(message_type, timeout)` |
| | `wait_for_response(message, reply_type, timeout)` |

### Key Methods

| Method | Description |
|---|---|
| `connect()` | No-op; sets `connected_event` and `started_running = True` |
| `close()` | Clears `connected_event`, calls `on_close()` |
| `emit(message)` | Injects session, dispatches to `pyee` emitter |
| `wait_for_message(message_type, timeout)` | Awaits a single message of that type |
| `wait_for_response(message, reply_type, timeout)` | Emits a message and awaits the reply |
| `create_client()` | Returns `self` (backwards-compat shim) |
| `run_forever()` | Sets `started_running = True` (backwards-compat shim) |
| `run_in_thread()` | Calls `run_forever()` (backwards-compat shim) |

### Session Handling

Session injection side effects are identical to `FakeBus`: `emit()` populates `message.context["session"]` from `SessionManager`, and `on_message()` feeds incoming messages back through `Session.from_message()` / `SessionManager.update()`. Both imports are lazy so the class works without `ovos-bus-client` installed.

---

## `FakeMessage`

Drop-in replacement for `ovos_bus_client.Message`. Transparently proxies to the real `Message` class if `ovos-bus-client` is installed:

```python
from ovos_utils.fakebus import FakeMessage

msg = FakeMessage("skill:action", {"key": "value"}, {"session_id": "abc"})
```

| Attribute | Description |
|---|---|
| `msg_type` | Message type string |
| `data` | Payload dict |
| `context` | Context dict (includes session, source, destination) |

### Key Methods

| Method | Description |
|---|---|
| `serialize() → str` | JSON-encode the message |
| `FakeMessage.deserialize(value) → FakeMessage` | Construct from JSON string |
| `forward(msg_type, data)` | Create a message with the same context |
| `reply(msg_type, data, context)` | Create a reply (swaps source ↔ destination) |
| `response(data, context)` | Shorthand for `reply(msg_type + ".response", ...)` |
| `publish(msg_type, data, context)` | Forward without a target |

### `isinstance` Compatibility

`FakeMessage` uses a metaclass (`_MutableMessage`) that makes `isinstance(msg, FakeMessage)` return `True` for real `ovos_bus_client.Message` objects as well, so code that checks `isinstance(msg, FakeMessage)` works in both environments.

---

## `Message` (Deprecated)

`ovos_utils.fakebus.Message` is a deprecated alias for `FakeMessage`. Import from `ovos_bus_client` directly.

---

## `dig_for_message()`

Tries to import and call `ovos_bus_client.message.dig_for_message`. Returns `None` if `ovos-bus-client` is not installed.

---
[← Modules](modules.md) · [Home](index.md) · [Next →](events.md)
