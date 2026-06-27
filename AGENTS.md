# AGENTS.md — ovos-utils

Foundational, dependency-light utility library shared across the OpenVoiceOS ecosystem: logging, message bus helpers, events/scheduling, OCP media data types, language/text/SSML helpers, file/XDG paths, geolocation, OAuth, security hashing, process/thread helpers, and the `ovos-logs` log inspection CLI.

## Setup

```bash
pip install ovos-utils            # core only
pip install ovos-utils[extras]    # adds rapidfuzz, ovos-plugin-manager, ovos-config, ovos-workshop, ovos-bus-client, langcodes, timezonefinder, oauthlib, orjson, packaging
```

Core deps are intentionally minimal (pexpect, requests, json_database, kthread, watchdog, pyee, combo-lock, rich/rich-click, python-dateutil, ovos-spec-tools). Heavier integrations live behind the `extras` group and are imported lazily (e.g. `try: import orjson`).

## Test

```bash
pytest test/unittests
```

Install `[extras]` first — several tests (lang, oauth, network) need optional deps.

## Lint/Typecheck

Lint runs in CI via the gh-automations `lint.yml` reusable workflow. No local typecheck config.

## Layout

- `ovos_utils/` — flat module collection; each file is an independent utility area:
  - `log.py`, `log_parser.py` — logging + the `ovos-logs` CLI (console script `ovos-logs = ovos_utils.log_parser:ovos_logs`).
  - `messagebus.py`, `fakebus.py`, `events.py`, `process_utils.py`, `thread_utils.py` — bus client helpers, in-memory fake bus for tests, event container/scheduler, process state machine, killable daemons.
  - `ocp.py` — OCP media data types (`MediaEntry`, `Playlist`, `PluginStream`, `MediaType`, `PlaybackType`, state enums).
  - `parse.py`, `text_utils.py`, `ssml.py`, `bracket_expansion.py`, `dialog.py`, `lang/` (phonemes, visimes) — NLG/text/language helpers.
  - `file_utils.py`, `xdg_utils.py`, `xml_helper.py`, `json_helper.py`, `list_utils.py` — IO/data helpers.
  - `geolocation.py`, `network_utils.py`, `oauth.py`, `security.py`, `smtp_utils.py`, `sound.py`, `gui.py`, `device_input.py`, `system.py`, `metrics.py`, `time.py`, `skills.py`, `skill_installer.py`, `decorators.py` — misc subsystems.
- `test/unittests/` — pytest suite, one file per module.
- `requirements/requirements.txt`, `requirements/extras.txt` — dep manifests mirrored into `pyproject.toml`.

This is a library, not a plugin/skill: no OPM/`ovos.plugin.*` entry-point group, only the `ovos-logs` console script under `[project.scripts]`.

## Conventions (Org hard rules)

- Branches: work on `dev`, stable on `master`. NEVER use `main`.
- Never edit `ovos_utils/version.py` — gh-automations bumps semver from conventional-commit prefixes (`feat:`, `fix:`, `feat!:`).
- New repos private by default; do not make source public without asking.
- Commit identity: `JarbasAi <jarbasai@mailfence.com>`.
- CI is provided by `OpenVoiceOS/gh-automations` reusable workflows, referenced at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary in code/docs/commits (no history, no dates, describe current state only).

## Gotchas

- Many modules carry deprecation shims (`log_deprecation`); some symbols in `ocp.py` are kept only for downstream import compatibility (`ovos-bus-client`). Check `__all__` before removing.
- Optional deps are soft-imported; guard new optional integrations the same way and add them to `extras`, not core.
- `fakebus.py` is the standard test double for bus-dependent code — prefer it over mocking.
