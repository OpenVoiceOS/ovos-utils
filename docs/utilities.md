# Utilities

Reference for the remaining utility modules in `ovos_utils`.

---

## File Utilities (`ovos_utils.file_utils`)

### Path and Directory Helpers

#### `get_temp_path(*args) → str`

Return a path inside the system temp directory without creating it:

```python
from ovos_utils.file_utils import get_temp_path

path = get_temp_path("mycroft", "audio", "example.wav")
# → "/tmp/mycroft/audio/example.wav"
```

#### `get_cache_directory(folder) → str`

Return a cache directory path, preferring RAM (`/dev/shm`-based via `memory_tempfile`) on Linux. Creates the directory.

#### `ensure_directory_exists(directory, domain=None) → str`

Create `directory` (and optional `domain` subdirectory) with `0o777` permissions.

#### `to_alnum(skill_id) → str`

Convert a skill ID to alphanumeric characters only (non-alphanumeric → `_`).

### Resource Resolution

#### `resolve_ovos_resource_file(res_name, extra_res_dirs) → Optional[str]`

Locate a bundled resource file by searching in order:
1. Absolute path (if already absolute)
2. `extra_res_dirs`
3. `ovos_utils/res/`
4. `ovos_workshop/res/`
5. `ovos_gui/res/`
6. `mycroft/res/` (legacy)

#### `resolve_resource_file(res_name, root_path, config) → Optional[str]`

Locate a resource file by searching:
1. Absolute path
2. `~/.mycroft/<res_name>`
3. `<data_dir>/<res_name>` (from config)
4. `resolve_ovos_resource_file()`

### Vocab / Regex Loading

| Function | Description |
|---|---|
| `read_vocab_file(path) → List[List[str]]` | Read a `.voc` file, expanding `{alt1\|alt2}` templates |
| `load_regex_from_file(path, skill_id) → List[str]` | Load regexes from a `.rx` file, munging skill ID |
| `load_vocabulary(basedir, skill_id) → dict` | Load all `.voc` files from a directory tree |
| `load_regex(basedir, skill_id) → List[str]` | Load all `.rx` files from a directory |
| `read_value_file(filename, delim) → OrderedDict` | Read a 2-column CSV as key-value pairs |
| `read_translated_file(filename, data) → List[str]` | Read a file with `{key}` substitutions |

### `FileWatcher`

Watch files or directories for changes using `watchdog`:

```python
from ovos_utils.file_utils import FileWatcher

watcher = FileWatcher(
    files=["~/.config/mycroft/mycroft.conf"],
    callback=lambda path: print(f"Changed: {path}"),
    recursive=False,
    ignore_creation=True,
)

# Later:
watcher.shutdown()
```

Fires the callback with the modified file path when a file is created or modified (closed after write). Optional `ignore_creation=True` skips creation events.

---

## Network Utilities (`ovos_utils.network_utils`)

```python
from ovos_utils.network_utils import get_ip, is_connected_dns, is_connected_http
```

| Function | Description |
|---|---|
| `is_valid_ip(ip) → bool` | Validate an IPv4 or IPv6 address string |
| `get_ip() → str` | Local IPv4 address (without sending packets) |
| `get_external_ip() → str` | Public IPv4 address via HTTP |
| `is_connected_dns(host, port, timeout) → bool` | Check connectivity by TCP-connecting to a DNS server (default: Cloudflare/Google) |
| `is_connected_http(host) → bool` | Check connectivity via HTTP HEAD request |
| `check_captive_portal(host, expected_text) → bool` | Detect captive portals by comparing HTTP response body |

Default test URLs/IPs are read from `mycroft.conf["network_tests"]`. Built-in defaults:

```python
{
    "ip_url": "https://api.ipify.org",
    "dns_primary": "1.1.1.1",
    "dns_secondary": "8.8.8.8",
    "web_url": "http://nmcheck.gnome.org/check_network_status.txt",
    "web_url_secondary": "https://checkonline.home-assistant.io/online.txt",
    "captive_portal_url": "http://nmcheck.gnome.org/check_network_status.txt",
    "captive_portal_text": "NetworkManager is online"
}
```

> `is_connected()` is deprecated — use `is_connected_http()` or `is_connected_dns()` directly.

---

## Sound (`ovos_utils.sound`)

```python
from ovos_utils.sound import play_audio, get_sound_duration
```

### `play_audio(uri, play_cmd=None, environment=None) → Optional[subprocess.Popen]`

Play an audio file in a background subprocess. Returns the `Popen` object on success, `None` on failure.

Player selection (if `play_cmd` not specified):
1. Check `mycroft.conf` for `play_ogg_cmdline` / `play_wav_cmdline` / `play_mp3_cmdline`
2. Auto-detect: `sox play` → `ogg123` → `pw-play` → `paplay` / `aplay` → `mpg123`

Supports PulseAudio ducking: if `mycroft.conf["tts"]["pulse_duck"]` is `True`, sets `PULSE_PROP=media.role=phone` in the subprocess environment.

### `get_sound_duration(path, base_dir) → float`

Return sound duration in seconds. Supports WAV natively (via `wave` stdlib). For other formats, requires `ffprobe` or `mediainfo` on `PATH`.

---

## Thread Utilities (`ovos_utils.thread_utils`)

```python
from ovos_utils.thread_utils import create_daemon, wait_for_exit_signal
```

### `create_daemon(target, args, kwargs, autostart) → Thread`

Create and optionally start a daemon `threading.Thread`.

### `create_killable_daemon(target, args, kwargs, autostart) → kthread.KThread`

Create and optionally start a killable daemon thread (`kthread.KThread`). Supports forceful termination.

### `wait_for_exit_signal()`

Block the calling thread until `SIGTERM` or `SIGINT` is received. Used by OVOS service entry points to keep the main thread alive:

```python
from ovos_utils.thread_utils import wait_for_exit_signal

# Start services in daemon threads, then block:
wait_for_exit_signal()
```

### `@threaded_timeout(timeout)`

Decorator that runs the decorated function in a background thread with a timeout. Raises `Exception` if the timeout is exceeded:

```python
from ovos_utils.thread_utils import threaded_timeout

@threaded_timeout(timeout=10)
def slow_operation():
    ...
```

---

## XDG Utilities (`ovos_utils.xdg_utils`)

XDG Base Directory Specification helpers. All functions return `Path` objects (or `None` for `xdg_runtime_dir()`).

```python
from ovos_utils.xdg_utils import xdg_config_home, xdg_data_home, xdg_cache_home

config_dir = xdg_config_home() / "mycroft"   # ~/.config/mycroft
data_dir = xdg_data_home() / "mycroft"       # ~/.local/share/mycroft
cache_dir = xdg_cache_home() / "mycroft"     # ~/.cache/mycroft
```

| Function | Env var | Default |
|---|---|---|
| `xdg_config_home()` | `XDG_CONFIG_HOME` | `~/.config` |
| `xdg_data_home()` | `XDG_DATA_HOME` | `~/.local/share` |
| `xdg_cache_home()` | `XDG_CACHE_HOME` | `~/.cache` |
| `xdg_state_home()` | `XDG_STATE_HOME` | `~/.local/state` |
| `xdg_runtime_dir()` | `XDG_RUNTIME_DIR` | `None` |
| `xdg_config_dirs()` | `XDG_CONFIG_DIRS` | `[/etc/xdg]` |
| `xdg_data_dirs()` | `XDG_DATA_DIRS` | `[/usr/local/share, /usr/share]` |

Environment variable values are only used if they are absolute paths; relative paths fall back to the default.
