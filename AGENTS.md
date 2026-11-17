# AGENTS.md

Conventions for AI coding agents (internal and community) working in this
repository.

## What this repo is

`ovos-utils` is the lowest-level shared utility package in the OVOS stack.
It covers logging, process management, threading helpers (including the
killable-daemon primitive used by `ovos-workshop`), XDG path resolution,
and `fakebus`, an in-process, no-websocket stand-in for
`ovos_bus_client.MessageBusClient` used by tests and standalone tooling
throughout the ecosystem.

It has almost no OVOS-specific dependencies of its own (its `extras` group
is what pulls in `ovos-plugin-manager`, `ovos-config`, `ovos-workshop`, and
`ovos_bus_client` for the optional higher-level helpers). Nearly every
other OVOS package depends on the base install of this one, so a behavior
change here is felt ecosystem-wide.

## Ground rules

- Work on a feature branch. Never push to `dev` or `master` directly.
- Open pull requests against `dev` as **drafts** until CI is green and the
  change is ready for review.
- One commit per PR. Squash before pushing if history accumulates.

- Use conventional commit prefixes (`fix:`, `feat:`, `refactor:`, `docs:`,
  `test:`, `chore:`). Reserve `feat:` for changes a user or downstream
  consumer can actually observe.
- Never hand-edit `ovos_utils/version.py`. CI computes and bumps the version
  from conventional commit history.

- Every PR description and issue you write or edit carries an AI-authorship
  disclosure at the top, naming the exact model used, and states the text is
  not human-reviewed.

## Dependencies

- Use `uv`, never `pip`, for installing and resolving dependencies.
- Pin floors only, and always allow prereleases: `>=X.Y.Za1`.

- All dependency and metadata declarations live in `pyproject.toml`. A
  `uv.lock` file is present in this repo for local dev reproducibility
  only. It is not a substitute for floor pins in `pyproject.toml` and
  should not be hand-edited. Regenerate it with `uv lock` if it drifts.

- Never install a dependency from a git URL. Publish an alpha to PyPI and
  depend on that.
- Keep the base install (no `extras`) free of hard OVOS-internal
  dependencies. That is what lets low-level tooling and other packages'
  test suites depend on `ovos-utils` without pulling in the rest of the
  stack. New functionality that needs `ovos-config`, `ovos_bus_client`, or
  `ovos-plugin-manager` belongs behind the `extras` group.

## Testing

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[extras]"
uv pip install pytest pytest-cov
pytest test/unittests
```

There is no `test` extra in `pyproject.toml`; test-only dependencies
(`pytest`, `pytest-cov`) are installed directly rather than through an
extras group.

A regression test for a bug must be shown to fail against the code before the
fix and pass after it. A test that passes against unfixed code proves
nothing and does not satisfy this gate.

## Docs discipline

Any change that touches observable behavior updates `README.md` and the
relevant file under `docs/` (`fakebus.md`, `events.md`, `log.md`,
`process-utils.md`, `utilities.md`) in the same PR.

Also add a version-stamped entry at the top of `docs/prerelease-quirks.md`
describing the change (create the file if it does not exist yet), newest
entry first.

## Repo-specific notes

- `ovos_utils.fakebus.FakeBus` must keep behaving like the real
  `MessageBusClient` API (same method names, same event semantics) without
  opening a websocket. It is what lets skills and plugins across the
  ecosystem be unit-tested without a running messagebus. Any divergence
  from the real client's observable behavior is a bug even if `fakebus`'s
  own tests pass.

- The `ovos-logs` console script (declared in `[project.scripts]`) points
  at `ovos_utils.log_parser:ovos_logs`. It lives inside the `ovos_utils`
  package itself. An empty `ovos_logs_console_script` file exists at the
  repo root but is not referenced by `pyproject.toml`'s
  `[tool.setuptools.packages.find]` (`include = ["ovos_utils*"]`). Don't
  assume it is where the script's code lives.

- `test/unittests` is the real test path (not bare `test/`). Point test
  commands and CI config at that directory.
