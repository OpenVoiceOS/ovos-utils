# Suggestions — `ovos-utils`

_Last updated: 2026-03-11 by Claude Sonnet 4.6_

> Each entry is backed by evidence from the source code and includes specific file/line citations.

---

### 1. Fix the OAuth token expiry check and add `None` guard

**Problem**: `get_oauth_token` in `ovos_utils/oauth.py:146` uses `>=` instead of `<=` when
comparing `expires_at` with the current time, meaning valid tokens are always refreshed.
Additionally, `token_data` is accessed without a `None` guard on line 144, causing `TypeError`
when a token does not exist.

**Proposed Solution**:
1. Change `token_data["expires_at"] >= time.time()` to `token_data["expires_at"] <= time.time()`.
2. Add an early return: `if token_data is None: return None` before the key access.
3. In `refresh_oauth_token` line 120, pull `expires_in` from `new_token_data` not `token_data`.

**Estimated Impact**: High correctness — fixes silent infinite refresh loops and prevents crashes.

---

### 2. Replace `inspect.stack()` in every log call with a lazy-logger registry

**Problem**: `LOG._get_real_logger()` (`ovos_utils/log.py:138-169`) calls `inspect.stack()` on
every single log statement.  `inspect.stack()` is expensive and runs even when the message would
be filtered out by the log level.  This adds measurable latency to every hot path in OVOS
services.

**Proposed Solution**: Pre-create loggers per module/function at first use (using `sys._getframe()`
with a fixed depth which is cheaper than `inspect.stack()`), or accept an explicit `name` argument
to `LOG.debug/info/warning/error` to eliminate dynamic stack inspection entirely.  Alternatively,
expose `LOG.get_logger(name)` and have callers cache the result as a module-level variable.

**Estimated Impact**: High performance — reduces log overhead across the entire codebase.

---

### 3. Split `log_parser.py` into a data model module and a CLI module

**Problem**: `ovos_utils/log_parser.py` is 670+ lines mixing `LogLine`, `Frame`, `Traceback`, and
`OVOSLogParser` (data model/parser) with Click commands `slice`, `list`, `show`, `reduce` (CLI).
This makes unit testing the parser without invoking Click impossible, and the file is too large for
a single responsibility.

**Proposed Solution**:
- `ovos_utils/log_parser.py` — keep only `LogLine`, `Frame`, `Traceback`, `OVOSLogParser`,
  `get_last_load_time`, `parse_timeframe`, etc.
- `ovos_utils/log_cli.py` (or move to `ovos_logs_console_script/`) — house the Click commands.
- Move the module-level `Configuration()` call into the CLI entry point so the data model module
  has no config dependency at import time.

**Estimated Impact**: Medium — improves testability and separation of concerns.

---

### 4. Replace `distutils.spawn.find_executable` with `shutil.which`

**Problem**: `ovos_utils/device_input.py:15` and `ovos_utils/sound.py:8` import
`from distutils.spawn import find_executable`. `distutils` was removed in Python 3.12, breaking
imports on modern Python. `shutil.which` is the stdlib replacement and is already used in
`system.py:285`.

**Proposed Solution**: Replace all `from distutils.spawn import find_executable` with
`from shutil import which as find_executable` (or just use `shutil.which` directly).

**Estimated Impact**: Low effort, high correctness on Python 3.12+.

---

### 5. Refactor `_build_linput_devices_list` to single-pass parsing

**Problem**: `ovos_utils/device_input.py:18-68` iterates `proc_output.splitlines()` four separate
times to collect device name, kernel path, group, and capabilities.  This is fragile because the
lists are built independently, so any mismatch in line counts (missing field for a device) will
cause an `IndexError` at line 65-67.

**Proposed Solution**: Parse in a single pass, accumulating a per-device dict that is appended to
`libinput_devices_list` when the device block is complete.  This also eliminates the length-mismatch
bug and reduces memory allocation.

**Estimated Impact**: Medium — fixes a latent `IndexError` bug and improves robustness.

---

### 6. Upgrade certificate generation in `security.py` to 2048-bit RSA and SHA-256

**Problem**: `ovos_utils/security.py:45` generates 1024-bit RSA keys and signs certificates with
SHA-1 (line 61). Both are cryptographically deprecated by NIST and rejected by modern clients
(browsers, Python's `ssl` module with strict settings).  A `TODO` comment already acknowledges
the SHA-1 issue.

**Proposed Solution**: Change `k.generate_key(crypto.TYPE_RSA, 1024)` to at least 2048 bits, and
replace `cert.sign(k, 'sha1')` with `cert.sign(k, 'sha256')`.

**Estimated Impact**: Critical security — self-signed certificates with 1024-bit keys will be
rejected by modern TLS clients.

---

### 7. Add type annotations and docstrings to `json_helper.py` and `xml_helper.py`

**Problem**: Neither `ovos_utils/json_helper.py` nor `ovos_utils/xml_helper.py` have any type
annotations or module-level docstrings.  These are utility modules used widely across the OVOS
ecosystem.

**Proposed Solution**: Add full PEP 484 type annotations to all public functions. Add module-level
docstrings explaining purpose and public API surface. Run `mypy --strict` on both files.

**Estimated Impact**: Low effort, high long-term benefit for IDE support and static analysis.

---

### 8. Introduce `FileEventHandler._changed_files` as a `set`

**Problem**: `ovos_utils/file_utils.py:416,424,434` uses a `list` for `_changed_files` membership
tests (`in`/`not in`), giving O(n) lookup time.  Under heavy file activity (e.g., config reload
storms) this could degrade performance.

**Proposed Solution**: Change `self._changed_files = []` to `self._changed_files = set()` and
update `append`/`remove` calls to `add`/`discard`.

**Estimated Impact**: Low effort, performance improvement for high-frequency file events.

---

### 9. Validate `Playlist` position changes through a single mutation hook

**Problem**: `ovos_utils/ocp.py:596-603` — `_validate_position` silently resets to 0 on invalid
position and logs an error, but does not raise.  Callers of `next_track`/`prev_track` cannot
distinguish a successful advance from a silent reset.  Also, `length` recomputes the entire entry
sum on every access (line 381).

**Proposed Solution**:
- Raise `IndexError` in `_validate_position` (or return a bool) rather than silently resetting.
- Cache `_length` as an instance attribute, invalidated in `add_entry`, `remove_entry`, `replace`,
  and `clear`.

**Estimated Impact**: Medium — improves correctness of playlist navigation and performance.

---

### 10. Remove double-deprecation pattern from `system.py` deprecated functions

**Problem**: `ntp_sync`, `system_shutdown`, `system_reboot`, `ssh_enable`, `ssh_disable`, and
`restart_mycroft_service` in `ovos_utils/system.py:38-127` each call `warnings.warn` inside the
function body **and** have the `@deprecated` decorator. Every call emits two deprecation warnings.

**Proposed Solution**: Remove the explicit `warnings.warn(...)` calls from inside each deprecated
function body, relying solely on the `@deprecated` decorator which already handles warning
emission.

**Estimated Impact**: Low effort — eliminates user-visible warning noise.

---

### 11. Lazily import `pexpect` in `security.py`

**Problem**: `pexpect` is imported unconditionally at the top of `ovos_utils/security.py` (line 9)
for a single function (`sudo_exec`). If `pexpect` is not installed, the entire `security` module
fails to import, breaking all consumers even those that only use `encrypt`/`decrypt`.

**Proposed Solution**: Move `import pexpect` inside `sudo_exec` so it fails only when that
function is actually called.

**Estimated Impact**: Low effort — improves import robustness for environments without `pexpect`.

---

### 12. Add full type annotations to `SSMLBuilder` public API

**Problem**: `ovos_utils/ssml.py` — all methods of `SSMLBuilder` lack parameter type annotations,
return types, and docstrings. This is the main public API of the module and is used by TTS plugins
across the OVOS ecosystem.

**Proposed Solution**: Annotate every method. All builder methods return `SSMLBuilder` (fluent
interface), so the return type annotation is straightforward. Add per-method docstrings explaining
SSML tag semantics.

**Estimated Impact**: Low effort, high long-term benefit for consumers of the TTS plugin API.
