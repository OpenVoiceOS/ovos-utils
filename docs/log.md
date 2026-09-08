# Logging

**Module:** `ovos_utils.log`

---

## `LOG`

A class-based logger that acts as a drop-in replacement for `logging.Logger`. All methods are `@classmethod`, so it can be used without instantiation.

```python
from ovos_utils.log import LOG

LOG.debug("Debug message: %s", value)
LOG.info("Started")
LOG.warning("Watch out")
LOG.error("Something failed")
LOG.exception("Unhandled exception")
```

### Logger Name

The logger name is determined by inspection of the call stack — it includes the module, function, and line number of the caller, plus `LOG.name` as a prefix. This makes OVOS log lines self-identifying without manually passing a logger name.

```
2024-01-01 12:00:00.000 - OVOS - ovos_core.skills.skill_manager:load:123 - INFO - Loading skill
```

Set a custom prefix:

```python
LOG("my-service").info("Ready")
```

Or set the class-level name:

```python
LOG.name = "audio"
```

### Configuration

`LOG` reads from `mycroft.conf["logging"]`:

```json
{
  "logging": {
    "log_level": "DEBUG",
    "logs": {
      "path": "/opt/ovos/logs/",
      "max_bytes": 50000000,
      "backup_count": 6
    },
    "audio": {
      "log_level": "INFO",
      "logs": {
        "path": "/var/log/ovos/"
      }
    }
  }
}
```

Service-specific sections (e.g. `logging.audio`) override the global defaults for that service.

### Class Attributes

| Attribute | Default | Description |
|---|---|---|
| `name` | `$OVOS_DEFAULT_LOG_NAME` or `OVOS` | Logger name prefix |
| `level` | `$OVOS_DEFAULT_LOG_LEVEL` or `INFO` | Log level |
| `base_path` | `stdout` | Log directory (or `"stdout"` for console only) |
| `max_bytes` | `50_000_000` | Max log file size before rotation |
| `backup_count` | `3` | Number of rotated log files to keep |
| `diagnostic_mode` | `False` | If True, log the source bus message for each log call |

### `LOG.init(config)`

Apply configuration from a dict (as returned by `get_logs_config()`). Updates `base_path`, `max_bytes`, `backup_count`, `level`, and `diagnostic_mode`.

### `LOG.set_level(level)`

Update the log level for the class and all existing loggers.

---

## `init_service_logger(service_name)`

Initialize `LOG` for a named OVOS service. Sets `LOG.name`, calls `LOG.init()`, and registers a config watcher to reload the log level when `mycroft.conf` changes.

```python
from ovos_utils.log import init_service_logger

init_service_logger("audio")
```

Call this once at service startup. Afterwards, `LOG.info(...)` etc. will tag log lines with the service name and write to the configured log file.

---

## `get_logs_config(service_name, _cfg) → dict`

Resolve the logging configuration for a given service name by walking the `mycroft.conf["logging"]` hierarchy. Returns a dict with at least `{"level": "INFO"}`.

---

## `log_deprecation(log_message, deprecation_version, ...)`

Log a deprecation warning that identifies the external caller (not the deprecation site itself).

```python
from ovos_utils.log import log_deprecation

log_deprecation("Use new_method() instead", "2.0.0")
```

---

## `@deprecated(log_message, deprecation_version)`

Decorator that logs a deprecation warning on every call:

```python
from ovos_utils.log import deprecated

@deprecated("Use new_method() instead", "2.0.0")
def old_method():
    ...
```

---

## `get_log_path(service, directories) → Optional[str]`

Return the log directory path for a given service, as configured in `mycroft.conf`. If `directories` is provided, search that list instead of reading config.

## `get_log_paths(config) → Set[str]`

Return all configured log directories across all services.

## `get_available_logs(directories) → List[str]`

Return a list of log file basenames (e.g. `["audio", "skills", "bus"]`) found in the configured log directories.

---
[Home](index.md) · [Process Utilities →](process-utils.md)
