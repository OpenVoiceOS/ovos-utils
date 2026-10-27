# FakeBus

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

`AsyncFakeBus` — `ovos_utils/fakebus.py:351`

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

| Method | Description | Source |
|---|---|---|
| `connect()` | No-op; sets `connected_event` and `started_running = True` | `fakebus.py:409` |
| `close()` | Clears `connected_event`, calls `on_close()` | `fakebus.py:418` |
| `emit(message)` | Injects session, dispatches to `pyee` emitter | `fakebus.py:426` |
| `wait_for_message(message_type, timeout)` | Awaits a single message of that type | `fakebus.py:489` |
| `wait_for_response(message, reply_type, timeout)` | Emits a message and awaits the reply | `fakebus.py:513` |
| `create_client()` | Returns `self` (backwards-compat shim) | `fakebus.py:543` |
| `run_forever()` | Sets `started_running = True` (backwards-compat shim) | `fakebus.py:546` |
| `run_in_thread()` | Calls `run_forever()` (backwards-compat shim) | `fakebus.py:549` |

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
[← Process Utilities](process-utils.md) · [Home](index.md) · [Events →](events.md)
