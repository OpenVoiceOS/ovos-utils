# OVOS-utils

`ovos-utils` is a shared utility library for the OpenVoiceOS ecosystem. It provides
logging, process lifecycle management, a testing-friendly fake message bus, event
scheduling, file utilities, network checks, audio playback, and XDG path helpers.
Most OVOS packages, including `ovos-bus-client`, `ovos-config`, and `ovos-workshop`,
depend on it, so most projects get it as a transitive dependency.

## Install

```bash
pip install ovos-utils
```

## Usage

The library exposes many small, independent modules. Import only what you need.
For example, use `FakeBus` to test skill code without a live message bus:

```python
from ovos_utils.fakebus import FakeBus, FakeMessage

bus = FakeBus()

def on_utterance(message):
    print(message.data["utterances"])

bus.on("recognizer_loop:utterance", on_utterance)
bus.emit(FakeMessage("recognizer_loop:utterance", {"utterances": ["hello"]}))
```

See [docs/index.md](docs/index.md) for the full module overview, with links to
detailed pages on logging, process utilities, `FakeBus`, and event handling.
See [docs/prerelease-quirks.md](docs/prerelease-quirks.md) for what changed
since the last stable release.

## Command line: ovos-logs

`ovos-logs` is a helper tool that slices, lists, and reduces OVOS service logs.

- **`ovos-logs slice [options]`**. Slice logs for a time period. The default
  period runs from the last service start (`-s`) until now (`-u`). Pick specific
  logs with `-l` (default: all logs). Set the log directory with `-p` and the
  output file with `-f`.

  ```bash
  ovos-logs slice
  # Slice all logs from the last service start until now.

  ovos-logs slice -s 17:05:20 -u 17:05:25
  # Slice all logs between 17:05:20 and 17:05:25.

  ovos-logs slice -s 17:05:20 -u 17:05:25 -l skills
  # Slice only skills.log between 17:05:20 and 17:05:25.

  ovos-logs slice -s 17:05:20 -u 17:05:25 -f ~/testslice.log
  # Slice logs between 17:05:20 and 17:05:25 into ~/testslice.log.
  # Default output file: ~/slice_<timestamp>.log
  ```

- **`ovos-logs list [-e|-w|-d|-x] [options]`**. List log lines by severity
  (error, warning, debug, exception). Specify at least one level. You can combine
  several. Set the time range with `-s` and `-u` (default: last service start
  until now). Pick specific logs with `-l` (default: all logs).

  ```bash
  ovos-logs list -x
  # List EXCEPTION-level lines (with tracebacks) from the last service start until now.

  ovos-logs list -w -e -s 20-12-2023 -l bus -l skills
  # List WARNING and ERROR lines from bus.log and skills.log since 20 December 2023.
  ```

- **`ovos-logs reduce [options]`**. Shrink logs to a target size in bytes, or
  remove entries before a given date. Pick specific logs with `-l` (default: all
  logs). Set the log directory with `-p`.

  ```bash
  ovos-logs reduce
  # Shrink all logs to 0 bytes.

  ovos-logs reduce -s 1000000
  # Shrink all logs to about 1 MB, keeping the latest entries.

  ovos-logs reduce -d "1-12-2023 17:00"
  # Shrink all logs to entries after the given date and time.

  ovos-logs reduce -s 1000000 -l skills -l bus
  # Shrink skills.log and bus.log to about 1 MB each.
  ```

- **`ovos-logs show -l <servicelog>`**. Print the contents of a log file.

  ```bash
  ovos-logs show -l bus
  # Print the contents of bus.log.
  ```

  The logs shown depend on which log files exist in the log folder.

## Related projects

- [OpenVoiceOS/ovos-bus-client](https://github.com/OpenVoiceOS/ovos-bus-client). The real message bus client that `FakeBus` and `FakeMessage` stand in for during testing.
- [OpenVoiceOS/ovos-config](https://github.com/OpenVoiceOS/ovos-config). Reads and writes `mycroft.conf`, the configuration file used by `LOG`, `PIDLock`, and the network utilities.
- [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop). The skill framework built on `EventContainer`, `RuntimeRequirements`, and the other utilities in this library.

## License

Apache License 2.0. See [LICENSE](LICENSE).
