
# Maintenance Report — `ovos-utils`

## [2026-03-11] — Fix build failures and address CI/CD audit

### Changes
- **`ovos_utils/thread_utils.py`** — Moved `import kthread` inside functions. This fixes `AttributeError: module 'ovos_utils.version' has no attribute '__version__'` during `python -m build` by allowing the package to be partially imported in isolated environments without all dependencies present.
- **`ovos_utils/skill_installer.py`** — Added `"-y"` flag to `uv pip uninstall` to ensure non-interactive execution, matching the pip fallback.
- **`ovos_utils/ocp.py`** — Added `__all__` to restore `from ovos_utils.ocp import *` functionality, which was broken by the `MediaType` deprecation shim.
- **`ovos_utils/ocp.py`** — Fixed `Playlist.add_entry` to correctly increment `position` *after* insertion, ensuring the logical selection remains on the same track when inserting before it.
- **`test/unittests/test_ocp.py`** — Updated assertions to verify that logical track selection is preserved during playlist insertions.
- **`test/unittests/test_dialog.py`** — Fixed `test_get_dialog_none_lang_config_import_error` to use `sys.modules` patching for `ovos_config` and removed broad `try/except` block.
- **`test/unittests/test_bracket_extra.py`** — Moved `Word` instance creation outside `catch_warnings` to prevent false positives in deprecation tests.
- **`test/unittests/test_device_input.py`** — Updated patch targets to `ovos_utils.device_input.find_executable` to correctly stub module-local imports.
- **`test/unittests/test_smtp_utils.py`** — Replaced broad `try/except` with explicit `sys.modules` mock for `ovos_config` to ensure test failures are surfaced.
- **`pyproject.toml`** — Added `python-dateutil` to core dependencies as it is required by `ovos_utils/time.py`.
- **`.github/workflows/build-tests.yml`** — Changed `install_extras` to `extras` to match `pyproject.toml` and ensure test dependencies are available.
- **`.github/workflows/python-support.yml`** — Removed redundant and deprecated workflow to resolve name collisions in CI.
- **`ovos_utils/log.py`** — Added `os.path.isdir` check in `get_available_logs` to prevent `FileNotFoundError` when log directories are missing (critical for environments like CI).
- **`ovos_utils/skill_installer.py`** — Implemented robust package name extraction and normalization using `packaging` library; improved error messaging for failed pip operations when `print_logs=True`.
- **`ovos_utils/thread_utils.py`** — Aligned `create_killable_daemon` return type annotation with docstring and used `TYPE_CHECKING` for `kthread`.
- **`pyproject.toml`** — Added `packaging` to `extras` dependencies.
- **`test/unittests/test_dialog.py`** — Improved `TestMustacheDialogRenderer` with failure mode coverage and deterministic selection testing; tightened `join_list` assertions and verified language fallback in `get_dialog`.
- **`test/unittests/test_ocp.py`** — Suppressed `DeprecationWarning` from `ovos_utils.ocp` during test collection.
- **`test/unittests/test_smtp_utils.py`** — Refactored `test_send_email_raises_when_no_config` to avoid patching `builtins.__import__`.
- **`test/unittests/test_device_input.py`** — Refined `distutils` stubbing logic to be less intrusive.

### Rationale
Fixed critical build-time attribute error and addressed multiple security/correctness findings from CodeRabbit audit.

### Verification
- `uv run pytest test/ -v` — All 897 tests passed.
- `python3 -c "import sys; sys.path.insert(0, '.'); import ovos_utils.version; print(ovos_utils.version.__version__)"` — Successfully returns version even with missing dependencies.

### AI Transparency Report
- **AI Model**: gemini-2.0-flash-thinking
- **Actions Taken**: Diagnosed `AttributeError` during build as a dependency issue in `__init__.py` chain, implemented lazy imports, and applied targeted fixes to test suite based on audit feedback.
- **Oversight**: Verified locally via pytest and manual import tests.

---

## [2026-03-11] — AUDIT.md bug fixes (20 confirmed fixes across 10 files)

### Changes
- **`oauth.py:143`** — Added `None` guard before accessing `token_data["expires_at"]`; fixes `TypeError` when token is absent.
- **`oauth.py:146`** — Fixed inverted expiry comparison: `>=` changed to `<=`; tokens were being refreshed on every call while still valid.
- **`oauth.py:120`** — Fixed `expires_in` read from stale `token_data` instead of `new_token_data` after a successful refresh.
- **`network_utils.py:94`** — Fixed operator precedence bug: `cfg.get("dns_primary" or ...)` split into `cfg.get("dns_primary") or cfg.get(...)` so fallback key is actually used.
- **`network_utils.py:124`** — Bare `except:` changed to `except Exception:`.
- **`skill_installer.py:336`** — Added `if proc.stderr:` guard before `.read()` to prevent `AttributeError` when `print_logs=True`.
- **`lang/__init__.py:17`** — Fixed `split("-", 2)` unpacked into 2 variables; changed to `split("-", 1)` to avoid `ValueError` on tags like `zh-Hant-TW`.
- **`lang/__init__.py:13,32`** — Bare `except:` changed to `except Exception:`.
- **`log_parser.py:144`** — `@classmethod` `parse` renamed first argument from `self` to `cls`.
- **`log_parser.py:145`** — `log_line.rstrip("\n")` result now assigned back: `log_line = log_line.rstrip("\n")`.
- **`log_parser.py:158`** — `@classmethod` `parse_file` renamed first argument from `self` to `cls` and updated `self.parse`/`self.LOG_PATTERN` references.
- **`log_parser.py:181`** — Blank-line skip check updated from `== "\n"` to `not log.message.strip()` to match post-rstrip empty strings.
- **`log_parser.py:386,521`** — `open(file, 'w')` writability tests changed to `open(file, 'a')` to prevent truncating log files; bare `except:` changed to `except Exception:`.
- **`geolocation.py:87`** — `if lat and lon:` changed to `if lat is not None and lon is not None:` to handle zero coordinates correctly.
- **`file_utils.py:416`** — `_changed_files` changed from `list` to `set`; `.append()` → `.add()`, `.remove()` → `.discard()`, `except:` → `except Exception:`.
- **`fakebus.py:27,140,208`** — All three bare `except:` changed to `except Exception:`.
- **`device_input.py:74,104`** — Bare `except:` changed to `except Exception:`.
- **`xml_helper.py:33`** — Bare `except:` changed to `except Exception:`.
- **`security.py:64-67`** — Two `open(...).write(...)` calls without context manager replaced with `with open(...) as f: f.write(...)`.
- **`test/unittests/test_oauth.py`** — Updated tests to reflect correct expiry semantics and added `expires_in` to `new_token_data` fixture.

### Rationale
All fixes address confirmed bugs documented in `AUDIT.md`. No behavioural changes beyond correcting the described defects.

### Verification
- `uv run pytest test/ --cov=ovos_utils --cov-report=term-missing` — 897 passed, 1 skipped, coverage 85%.

### AI Transparency Report
- **AI Model**: claude-sonnet-4-6
- **Actions Taken**: Read all affected source files, applied minimal targeted fixes to each confirmed bug, updated two tests that encoded the old buggy behaviour.
- **Oversight**: Human review required before committing.

---

## [2026-03-08] — Initial compliance scaffold

### Changes
- Created `QUICK_FACTS.md` with machine-readable package metadata.
- Created `FAQ.md` with common Q&A.
- Created `MAINTENANCE_REPORT.md` (this file) as the change log.
- Created `SUGGESTIONS.md` with initial improvement proposals.
- Created `docs/index.md` as the documentation entry point (if missing).

### Rationale
Establishing the required file set mandated by `AGENTS.md` for all active workspace repositories.

### Verification
- All required files exist at repo root and `docs/` folder.
- No existing content was overwritten.

### AI Transparency Report
- **AI Model**: Claude Sonnet 4.6
- **Actions Taken**: Generated boilerplate compliance scaffold (QUICK_FACTS, FAQ, MAINTENANCE_REPORT, SUGGESTIONS, docs/index).
- **Oversight**: Files are stubs — human review and enrichment required before treating as authoritative.
