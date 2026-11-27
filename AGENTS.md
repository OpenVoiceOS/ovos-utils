# AGENTS.md

`ovos-utils` is the lowest shared library of OpenVoiceOS: logging, process status, threads, XDG paths, and `FakeBus`, a bus with no websocket for tests. Almost every OVOS package depends on it, so a change in behaviour here reaches the whole stack.

## Map

| Path | Holds |
| :--- | :--- |
| `ovos_utils/fakebus.py` | `FakeBus`, `AsyncFakeBus` and `FakeMessage` |
| `ovos_utils/log.py`, `ovos_utils/log_parser.py` | `LOG`, and the `ovos-logs` command |
| `ovos_utils/process_utils.py` | `ProcessStatus`, `RuntimeRequirements` and `PIDLock` |
| `ovos_utils/metrics.py`, `ovos_utils/prometheus.py` | Latency histograms and the opt-in `/metrics` endpoint |
| `ovos_utils/*.py` | One module for each helper group. `docs/modules.md` lists them. |
| `test/unittests` | The tests |
| `docs/` | The documentation. Start at `docs/index.md`. |

## Setup and test

```bash
uv venv
uv pip install --prerelease=allow -e ".[extras]" pytest pytest-cov
.venv/bin/pytest test/unittests
```

There is no `test` extra. CI (`build-tests.yml`) installs the `extras` extra and runs `test/unittests`.

## Rules

- Open pull requests against `dev`, as drafts until CI passes. Never push to `dev` or `master`.
- Use conventional commits. Use `feat:` only for a change that a user or a consumer can see.
- Do not edit `ovos_utils/version.py`. CI sets the version from the commit history.
- Pull requests are squash-merged. Do not squash by hand.
- Put an AI disclosure at the top of each PR and issue that an agent writes. Name the exact model and say that no human reviewed the text.
- Use `uv`, not `pip`. Use floor pins with prereleases (`>=X.Y.Za1`). Use no git URL dependency. All metadata is in `pyproject.toml`.
- The base install depends on no other OVOS package except `ovos-spec-tools`. Code that needs `ovos-config`, `ovos_bus_client` or `ovos-plugin-manager` goes behind the `extras` extra.
- `FakeBus` behaves like `MessageBusClient`: the same methods and the same delivery, with no websocket. A difference from the real client is a bug, also when the `fakebus` tests pass.
- A regression test fails on the code before the fix and passes after it.
- A change in behaviour updates the page in `docs/` that describes it, in the same PR.
- When the behaviour differs from the last stable release, the PR also updates `docs/prerelease-quirks.md`.
