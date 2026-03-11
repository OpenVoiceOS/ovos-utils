# Process Utilities

**Module:** `ovos_utils.process_utils`

---

## `RuntimeRequirements`

Dataclass that declares what external resources a skill or plugin requires before it can be loaded and while it handles utterances.

```python
from ovos_utils.process_utils import RuntimeRequirements

class MySkill:
    runtime_requirements = RuntimeRequirements(
        network_before_load=False,
        internet_before_load=False,
        requires_internet=False,
        requires_network=False,
        no_network_fallback=True,
    )
```

| Field | Default | Description |
|---|---|---|
| `network_before_load` | `True` | Wait for network before loading the skill |
| `internet_before_load` | `True` | Wait for internet before loading the skill |
| `gui_before_load` | `False` | Wait for GUI before loading the skill |
| `requires_internet` | `True` | Internet needed to handle utterances |
| `requires_network` | `True` | Network needed to handle utterances |
| `requires_gui` | `False` | GUI needed to handle utterances |
| `no_internet_fallback` | `False` | Has a cached/offline fallback mode |
| `no_network_fallback` | `False` | Has a cached/offline fallback mode |
| `no_gui_fallback` | `True` | Can work voice-only without GUI |

The default values (`True` for `network_before_load` / `internet_before_load`) preserve backwards compatibility with older skills that assumed network availability at load time.

---

## `ProcessState`

`IntEnum` representing OVOS service lifecycle stages. Ordered so that `>= ProcessState.ALIVE` works as a range check:

| Value | Name | Description |
|---|---|---|
| 0 | `NOT_STARTED` | Process not yet started |
| 1 | `STARTED` | Process started (basic init done) |
| 2 | `ERROR` | Non-recoverable error |
| 3 | `STOPPING` | Shutdown in progress |
| 4 | `ALIVE` | Core setup complete |
| 5 | `READY` | Fully loaded and ready to serve |

---

## `ProcessStatus`

Tracks the lifecycle state of an OVOS service. Registers message bus handlers for status queries and fires optional callbacks on state transitions.

```python
from ovos_utils.process_utils import ProcessStatus, StatusCallbackMap

def on_ready():
    LOG.info("Service ready!")

status = ProcessStatus(
    name="audio",
    bus=bus,
    callback_map=StatusCallbackMap(on_ready=on_ready),
    namespace="mycroft",
)

status.set_started()
status.set_alive()
status.set_ready()   # fires on_ready()
```

### Bus Events Registered

| Event | Response |
|---|---|
| `{namespace}.{name}.is_alive` | `{"status": bool}` — True if state ≥ ALIVE |
| `{namespace}.{name}.is_ready` | `{"status": bool}` — True if state ≥ READY |
| `mycroft.{name}.all_loaded` | Same as `is_ready` (backwards compat) |

### State Transition Methods

| Method | Sets state to | Fires callback |
|---|---|---|
| `set_started()` | `STARTED` | `on_started` |
| `set_alive()` | `ALIVE` | `on_alive` |
| `set_ready()` | `READY` | `on_ready` |
| `set_stopping()` | `STOPPING` | `on_stopping` |
| `set_error(err)` | `ERROR` | `on_error(err)` |

### `StatusCallbackMap`

Named tuple with optional fields: `on_started`, `on_alive`, `on_ready`, `on_error`, `on_stopping`. All default to `None`.

---

## `MonotonicEvent`

A `threading.Event` subclass with a timeout implementation based on `time.monotonic` to avoid being affected by system clock changes.

```python
from ovos_utils.process_utils import MonotonicEvent

event = MonotonicEvent()
result = event.wait(timeout=5.0)  # monotonic-safe timeout
```

`wait_timeout(timeout)` polls in 0.1-second increments until the event is set or the monotonic deadline passes.

---

## `PIDLock`

Creates and maintains a PID file in the system temp directory. On construction, kills any existing process with the same service name, then writes the current PID.

```python
from ovos_utils.process_utils import PIDLock

lock = PIDLock("skills")  # creates /tmp/mycroft/skills.pid
```

Registers `SIGINT` / `SIGTERM` handlers to delete the PID file on exit. The directory is resolved from `ovos_config` if available, otherwise from `OVOS_CONFIG_BASE_FOLDER` env var (default: `mycroft`).

---

## `Signal`

Chainable POSIX signal handler. Each instance installs a user function as the new handler and calls the previous handler in LIFO order. Restored on garbage collection.

---

## `reset_sigint_handler()`

Reset `SIGINT` to the default Python handler. Needed when starting OVOS services from shell scripts that have modified the signal mask.
