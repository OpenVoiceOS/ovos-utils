
# Maintenance Report — `ovos-utils`

## [2026-03-11] — AUDIT.md bug fixes (13 confirmed bugs)

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
