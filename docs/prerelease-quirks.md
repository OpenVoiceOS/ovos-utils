# Prerelease quirks
<!-- agent-hint
covers: the behaviours of a dev alpha that differ from the last stable release, and what to do about each one
source: pyproject.toml, ovos_utils/fakebus.py, ovos_utils/prometheus.py, ovos_utils/file_utils.py
generated: no
verify: python3 docs/check_page.py docs/prerelease-quirks.md && grep -q '"rich>=13.7"' pyproject.toml && grep -v '^verify:' docs/prerelease-quirks.md | grep -qF '`rich>=13.7`'
see: index.md
-->

This page lists the behaviours of a `dev` alpha that differ from the last stable release. Read it before you report a bug on an alpha. `CHANGELOG.md` lists each change by version.

## Dependencies

- `ovos-utils` depends on `ovos-spec-tools`. `fakebus.Message` is a subclass of `ovos_spec_tools.Message`. The API does not change.
- `json_database` 1.x is accepted.
- No module imports `distutils`, so `ovos-utils` imports on Python 3.12 and later.
- The `rich` requirement is `rich>=13.7`, with no upper bound. An environment with rich 14 or 15 resolves.

## FakeBus

- `AsyncFakeBus` is an asyncio form of `FakeBus`. See [fakebus.md](fakebus.md).

- `FakeBus` and `AsyncFakeBus` dispatch both spellings of a migrated topic and of an intent topic. A test that counts deliveries can see a second handler call. See [fakebus.md](fakebus.md#topic-bridges).
- A second `on()` or `once()` with the same topic and handler does not add a listener. The handler fires once.

## Files

- A `FileEventHandler` fires only for changes to its own file.
- `FileWatcher` accepts a path that does not exist yet. It starts to watch when the file appears.

## Metrics

- `ovos_utils.prometheus` serves the opt-in `/metrics` endpoint. Nothing records or listens until `OVOS_METRICS_ENABLED` is set. See [metrics.md](metrics.md).

---
[← Metrics](metrics.md) · [Home](index.md)
