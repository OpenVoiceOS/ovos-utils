# ovos-utils
<!-- agent-hint
covers: what ovos-utils is, how to install it, and where each topic is documented
source: pyproject.toml, ovos_utils/fakebus.py
generated: no
verify: python3 docs/check_page.py README.md
see: docs/index.md
-->

`ovos-utils` is the shared utility library of OpenVoiceOS. It gives logging, process status, an in-process fake message bus for tests, event helpers, file and network helpers, XDG paths and the `ovos-logs` command. Most OVOS packages depend on it.

## Install

```bash
uv pip install --prerelease=allow ovos-utils
```

## Quickstart

Test a bus handler with `FakeBus`, with no messagebus running:

```python
from ovos_utils.fakebus import FakeBus, FakeMessage

bus = FakeBus()

def on_utterance(message):
    print(message.data["utterances"])

bus.on("recognizer_loop:utterance", on_utterance)
bus.emit(FakeMessage("recognizer_loop:utterance", {"utterances": ["hello"]}))
```

```text
['hello']
```

## Documentation

| Page | What you get there |
| :--- | :--- |
| [docs/index.md](docs/index.md) | The reading order of all pages |
| [docs/modules.md](docs/modules.md) | Each module and what it holds |
| [docs/fakebus.md](docs/fakebus.md) | How to test bus code with `FakeBus` and `AsyncFakeBus` |
| [docs/log.md](docs/log.md) | How to log with `LOG` |
| [docs/ovos-logs.md](docs/ovos-logs.md) | How to slice, list and shrink service logs |

## License

Apache License 2.0. See [LICENSE](LICENSE).
