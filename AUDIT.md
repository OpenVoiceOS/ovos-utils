# AUDIT.md — ovos-utils

_Last updated: 2026-03-11 by Claude Sonnet 4.6_

---

## Critical (bugs / correctness)

### `ovos_utils/oauth.py:146` — Inverted expiry check causes tokens to always be treated as expired
`get_oauth_token` checks `token_data["expires_at"] >= time.time()` to decide whether the token is
expired. The condition is backwards: `>=` means the token is treated as expired when the expiry
time is **in the future**, which causes tokens to be refreshed on every call while they are still
valid. The correct check is `token_data["expires_at"] <= time.time()`.

### `ovos_utils/oauth.py:143-149` — `None` token data not guarded before key access
`get_oauth_token` calls `db.get(token_id)` then immediately accesses `token_data["expires_at"]`
without checking whether `token_data` is `None` (token not found). If the token does
not exist this raises an unhandled `TypeError`.

### `ovos_utils/oauth.py:120` — `expires_at` calc uses wrong dict (`token_data` instead of `new_token_data`)
```python
new_token_data['expires_at'] = time.time() + token_data['expires_in']
```
`token_data['expires_in']` may not be present in the **original** stale `token_data`. The
refreshed response (`new_token_data`) normally carries `expires_in`; the code should use
`new_token_data['expires_in']`. If the key is missing this raises `KeyError`.

### `ovos_utils/network_utils.py:94-95` — Operator precedence bug in DNS config fallback
In `is_connected_dns`:
```python
return is_connected_dns(cfg.get("dns_primary" or _DEFAULT_TEST_CONFIG['dns_primary'])) or ...
```
The `or` is evaluated **inside** `cfg.get(...)`, so the call becomes `cfg.get("dns_primary")`
unconditionally — the fallback string is never used. The intent is:
```python
cfg.get("dns_primary") or _DEFAULT_TEST_CONFIG['dns_primary']
```

### `ovos_utils/fakebus.py:27-28` — Bare `except:` swallows all exceptions on `session_id` read
```python
try:
    self.session_id = kwargs["session"].session_id
except:
    pass  # don't care
```
A bare `except:` captures `SystemExit` and `KeyboardInterrupt`. Should be `except Exception:`.

### `ovos_utils/fakebus.py:207-208` — `FakeMessage.__eq__` uses bare `except:`
```python
except:
    return False
```
Masks all exceptions including interpreter-level signals. Should be `except Exception:`.

### `ovos_utils/device_input.py:74-75` — Bare `except:` in `_get_libinput_devices_list`
Using a bare `except:` instead of `except Exception:`.

### `ovos_utils/device_input.py:103-106` — Bare `except:` in `_get_xinput_devices_list`
Same pattern as above.

### `ovos_utils/device_input.py:62-68` — `IndexError` when list lengths diverge
`_build_linput_devices_list` builds four lists independently by iterating `proc_output` four times.
If any `Kernel`, `Group`, or `Capabilities` line is missing for a device, the lengths will
mismatch, and `input_device_kernel_path[i]` will raise an `IndexError`.

### `ovos_utils/geolocation.py:87` — Falsy check incorrectly rejects latitude/longitude of `0`
```python
if lat and lon:
    return get_reverse_geolocation(lat, lon, lang)
```
`lat` and `lon` are strings from the JSON response. The string `"0"` or `"0.0"` is falsy for
coordinates on the prime meridian or equator. Should be:
```python
if lat is not None and lon is not None:
```

### `ovos_utils/security.py:45` — RSA key size of 1024 bits is cryptographically weak
`k.generate_key(crypto.TYPE_RSA, 1024)` — 1024-bit RSA has been considered broken since 2012
(NIST SP 800-131A). Minimum recommended is 2048 bits. The `# TODO don't use sha1` comment on
line 61 also acknowledges that SHA-1 signing is insecure.

### `ovos_utils/security.py:64-67` — File handles not closed (`open(...).write(...)` without context manager)
```python
open(cert_path, "wt").write(...)
open(join(cert_dir, KEY_FILE), "wt").write(...)
```
These rely on the garbage collector to close the file handle. On some Python implementations the
file may be flushed/closed non-deterministically, causing truncated writes. Use `with open(...)`.

### `ovos_utils/log_parser.py:145` — `log_line.rstrip("\n")` result is discarded
```python
log_line.rstrip("\n")
```
`str.rstrip` returns a new string; the result is not assigned. Lines are parsed with trailing
newlines intact. Should be `log_line = log_line.rstrip("\n")`.

### `ovos_utils/log_parser.py:370-372` — File handle leaked when writing slice output
```python
Console(file=open(file, 'a')).print(table)
```
The file opened inside `Console(...)` is never explicitly closed, leaking a file descriptor on
every loop iteration. Same pattern at line 576.

### `ovos_utils/log_parser.py:597` — File opened without `with`, never closed
```python
pydoc.pager(open(log).read())
```
Should be `with open(log) as fh: pydoc.pager(fh.read())`.

### `ovos_utils/skill_installer.py:244-245` — `proc.stderr` is `None` when `print_logs=True` in `pip_install`
When `print_logs=True` the `Popen` is created without `stderr=PIPE`, so `proc.stderr` is `None`.
The `if stderr:` guard prevents a crash but the error message passed to `RuntimeError` is `None`,
giving useless diagnostics.

### `ovos_utils/version.py` — `AttributeError: module 'ovos_utils.version' has no attribute '__version__'` during build
In isolated build environments (like `python -m build`), `setuptools` tries to read the version
via `attr: ovos_utils.version.__version__`. Because `ovos_utils/__init__.py` imports `thread_utils`,
which in turn has a top-level `import kthread`, the build fails if `kthread` is not already
present in the host environment (even if it's listed in `dependencies`). This prevents the
package from being built or audited in clean environments. `kthread` should be a lazy import.

### `ovos_utils/skill_installer.py:316-319` — `uv pip uninstall` missing `-y` flag
The `uv` branch of the uninstall command does not include the `-y` (non-interactive) flag,
causing `Popen` to hang waiting for user confirmation in a non-interactive shell.
Match the pip fallback by adding `"-y"` to the `pip_args` list.

### `ovos_utils/lang/__init__.py:17` — `split("-", 2)` with two-variable unpack fails on 3-part BCP-47 tags
```python
a, b = lang_code.split("-", 2)
```
`str.split("-", 2)` with `maxsplit=2` can return up to three parts (e.g., `"zh-Hant-TW"` →
`["zh", "Hant", "TW"]`). Unpacking into two variables raises `ValueError: too many values to unpack`.

### `ovos_utils/log_parser.py:386-389` — `open(file, 'w')` truncates file to test writability
```python
try:
    with open(file, 'w') as f:
        pass
```
This destroys the file contents before any new content is written. If the subsequent write loop
fails, the original log file is lost. Use `os.access(file, os.W_OK)` instead.
Same pattern repeated at line 521.

---

## Performance

### `ovos_utils/log.py:138-169` — `inspect.stack()` called on every log message
`_get_real_logger()` calls `inspect.stack()` for every `LOG.debug/info/warning/error` call.
`inspect.stack()` is expensive (captures the full call stack). A new logger instance is looked up
or created per call via `create_logger`, which checks `cls._loggers` but still builds a name
string each time.

### `ovos_utils/device_input.py:18-68` — `proc_output.splitlines()` iterated four separate times
`_build_linput_devices_list` iterates the same string four times to collect four different fields.
A single pass collecting all fields simultaneously would be more efficient.

### `ovos_utils/file_utils.py:423-435` — `_changed_files` is a `list` used for membership tests
`event.src_path in self._changed_files` and `event.src_path not in self._changed_files` perform
O(n) membership checks on a list. A `set` would give O(1) lookups.

### `ovos_utils/log_parser.py:255-259` — Full file read then reversed for `get_last_load_time`
```python
for line in f.readlines()[::-1]:
```
`readlines()[::-1]` reads the entire log file into memory before reversing. For large log files
this wastes memory. A reverse-reading approach (seek to end, read chunks backwards) is better.

### `ovos_utils/ocp.py:381-383` — `Playlist.length` recomputes sum over all entries on every access
```python
return max(-1, sum([e.length for e in self.entries]))
```
`self.entries` iterates `self` and converts dicts, so `length` does O(n) work per property access.
A list comprehension creates a temporary list unnecessarily; use a generator expression. Ideally,
cache the value and invalidate on mutation.

### `ovos_utils/system.py:274-281` — `is_process_running` leaves `Popen` subprocess without cleanup
The code iterates `s.stdout` but never calls `s.wait()` or `s.communicate()`, potentially leaving
zombie processes on Linux. Should call `s.wait()` after the loop.

---

## Type Annotation Gaps

### `ovos_utils/json_helper.py` — No type annotations on any public function
`nested_get`, `nested_set`, `nested_delete`, `flatten_dict`, `flattened_get`, `flattened_set`,
`flattened_delete`, `invert_dict`, `merge_dict`, `load_commented_json`, `uncomment_json`,
`is_compatible_dict` — none have parameter or return type hints.

### `ovos_utils/xml_helper.py` — No type annotations on any public function
`etree2dict`, `xml2dict`, `load_xml2dict`, `dict2xml` — all lack type annotations.

### `ovos_utils/metrics.py` — `Stopwatch` class has no type annotations
Class attributes `timestamp` and `time` and all method return types are unannotated.

### `ovos_utils/file_utils.py:104-105` — `extra_res_dirs` typed as `list` not `Optional[List[str]]`
```python
def resolve_ovos_resource_file(res_name: str,
                               extra_res_dirs: list = None) -> Optional[str]:
```
Default `None` is not reflected in the annotation; should be `Optional[List[str]] = None`.

### `ovos_utils/dialog.py:206` — `items[-1]` not coerced to `str` in `join_list`
```python
" " + translate_word(connector, lang) + " " + items[-1]
```
`items[-1]` is not wrapped in `str()` while earlier items use `str(item)`. If the list contains
a non-string last element this raises `TypeError`.

### `ovos_utils/time.py:33` — `tz` param type hint is incorrect
```python
def now_local(tz: datetime.tzinfo = None) -> datetime:
```
`datetime.tzinfo` is a class, not an instance type. Should be `Optional[tzinfo]` where `tzinfo`
is imported from `datetime`.

### `ovos_utils/log_parser.py:265-285` — Multiple helper functions missing all type annotations
`valid_log(logs, paths)`, `parse_time(time_str)`, and
`get_timestamped_filename(basename, ext, basedir, timeformat)` all lack parameter and return
type annotations.

### `ovos_utils/ssml.py` — `SSMLBuilder` methods missing type annotations and docstrings
All public methods (`sub`, `emphasis`, `parts_of_speech`, `pause_by_strength`, `sentence`,
`say_emphasis`, `say_strong`, `say_weak`, `say_softly`, `say_auto_breaths`, `paragraph`, `audio`,
`pause`, `prosody`, `pitch`, `volume`, `rate`, `say`, `say_loud`, `say_slow`, `say_fast`,
`say_low_pitch`, `say_high_pitch`, `say_whispered`, `phoneme`, `voice`, `whisper`, `build`,
`remove_ssml`, `extract_ssml_tags`) lack parameter types, return types, and docstrings.

### `ovos_utils/ocp.py:188` — `MediaEntry.update` uses dunder methods directly
`self.__getattribute__(k)` and `self.__setattr__(k, v)` should be `getattr(self, k)` and
`setattr(self, k, v)` per Python convention.

---

## Code Smells / Debt

### `ovos_utils/security.py:9` — `pexpect` is a hard import for a rarely-used function
`pexpect` is imported unconditionally, but `sudo_exec` is a legacy helper that few code paths use.
If `pexpect` is not installed the entire `security` module fails to import. Should be a lazy
import inside `sudo_exec`.

### `ovos_utils/security.py:107-122` — `sudo_exec` default password is `"root"` — security smell
`sudo_exec(cmdline, passwd="root")` passes a plaintext password via subprocess with a hardcoded
default. This exposes the password in process listings. The default value should be removed.

### `ovos_utils/process_utils.py:113-116` — Dead code for Python < 3.7
The project requires Python 3.10+, making the `sys.version_info < (3, 7)` branch dead code.

### `ovos_utils/log.py:134` — Single-character loop variable `l` (ambiguous)
```python
for l in cls._loggers:
```
`l` is easily confused with `1` (one). Should be `logger_name` or similar.

### `ovos_utils/log.py:77-78` — `@classmethod` named `__init__` creates confusing API
Calling `LOG("name")` goes through `type.__call__`, invoking `__new__` then `__init__`. Since
`__init__` is a `@classmethod`, callers get `None` back instead of a logger instance. The intent
appears to be a factory call but the implementation is surprising.

### `ovos_utils/log_parser.py:144-155` — `@classmethod` first argument named `self` not `cls`
Both `OVOSLogParser.parse` and `OVOSLogParser.parse_file` use `self` as the first argument of a
`@classmethod`. This violates Python convention and is misleading.

### `ovos_utils/device_input.py:15-16` — `distutils.spawn.find_executable` is removed in Python 3.12
`from distutils.spawn import find_executable` — `distutils` was removed in Python 3.12. Should
use `shutil.which` instead (as `system.py` already does on line 285). Same issue in `sound.py:8`.

### `ovos_utils/network_utils.py:121-126` — Bare `except:` in `is_connected_http`
```python
except:
    pass
```
Should be `except Exception:`. Also, `status` is computed but never used — any successful HTTP
HEAD returns `True` regardless of status code.

### `ovos_utils/xml_helper.py:33-34` — Bare `except:` in `xml2dict`
```python
except:
    return {}
```
Silently returns `{}` for any error including parse failures, interpreter signals, or `MemoryError`.

### `ovos_utils/lang/__init__.py:13-14` — Bare `except:` in `standardize_lang_tag`
Should be `except Exception:`.

### `ovos_utils/lang/__init__.py:32-34` — Bare `except:` in `get_language_dir`
Should be `except Exception:`.

### `ovos_utils/file_utils.py:413` — `_events` assigned as string `'modified'` not a tuple
```python
self._events = ('modified')
```
`('modified')` is a `str`, not a single-element tuple. A tuple requires a trailing comma:
`('modified',)`. The membership test `event.event_type in self._events` accidentally works as a
substring check on `"modified"`, but this is unintentional and confusing.

### `ovos_utils/system.py:38-67` — Deprecated functions emit double deprecation warnings
`ntp_sync`, `system_shutdown`, `system_reboot`, `ssh_enable`, `ssh_disable`, and
`restart_mycroft_service` each call `warnings.warn` inside the function body **and** have the
`@deprecated` decorator, which also emits a warning. Two warnings are issued per call.

### `ovos_utils/log_parser.py:670+` — File is 670+ lines mixing data model and CLI commands
`LogLine`, `Frame`, `Traceback`, `OVOSLogParser` (data model) and Click commands `slice`, `list`,
`show`, `reduce` (CLI) are all in one file. These should be split into separate modules.

### `ovos_utils/log_parser.py:18-22` — Configuration loaded at module import time
```python
use24h = Configuration().get("time_format", "full") == "full"
date_format = Configuration().get("date_format", "DMY")
```
Values are frozen at startup; runtime configuration changes are ignored. Makes unit testing harder.

### `ovos_utils/ocp.py:667-693` — `if __name__ == "__main__"` block in library module
Executable demo code at the bottom of a library module should be removed or placed in an
example/script file.

### `ovos_utils/bracket_expansion.py:309` — Unresolved `TODO` in production code
```python
# TODO anything special about {sth}?
```
Known open question in `SentenceTreeParser._parse_expr`.

### `ovos_utils/dialog.py:22` — Magic number for `max_recent_phrases` with self-acknowledged TODO
```python
# TODO magic numbers are bad!
self.max_recent_phrases = 3
```
Should be a class constant or constructor parameter.

### `ovos_utils/events.py:252` — Unresolved `TODO` about null event name handling
```python
# TODO: Is a null name valid or should it raise an exception?
```

### `ovos_utils/ssml.py:73-74` — Amazon-specific SSML extension is not portable
`<amazon:effect vocal-tract-length...>` is an Amazon Alexa extension that will produce invalid
SSML on non-Alexa TTS engines. Callers have no way to know this is Amazon-only.

### `ovos_utils/parse.py:29` — LOG call used to print pip installation instructions
```python
LOG.warning("pip install rapidfuzz")
```
Outputs an installation instruction via the logger, which is unconventional and pollutes structured
logs with user-facing hints. Use `print()` or a separate user-facing message mechanism.

### `ovos_utils/list_utils.py:35` — Lambda assigned to variable violates PEP 8
```python
_flatten = lambda l: [item for sublist in l for item in sublist]
```
PEP 8 discourages assigning lambdas to variables; use a `def` statement. Also `l` is ambiguous.

### `ovos_utils/sound.py:123` — Missing blank line before `get_sound_duration` function (PEP 8)
No blank line separates the end of `play_audio` from the start of `get_sound_duration`.

### `ovos_utils/text_utils.py` — Missing two blank lines between top-level functions (PEP 8)
`camel_case_split`, `collapse_whitespaces`, `rm_parentheses`, `remove_accents_and_punct` are
separated by only one blank line each.

### Multiple files — Missing module-level docstrings
`bracket_expansion.py`, `json_helper.py`, `xml_helper.py`, `metrics.py`, `text_utils.py`,
`ssml.py`, `list_utils.py` all lack module-level docstrings explaining purpose and public API.
