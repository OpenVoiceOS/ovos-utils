# Read service logs with ovos-logs
<!-- agent-hint
covers: how to slice, list, shrink and show the OVOS service logs with the ovos-logs command
source: ovos_utils/log_parser.py, pyproject.toml ([project.scripts])
generated: no
verify: python3 docs/check_page.py docs/ovos-logs.md
see: modules.md
-->

`ovos-logs` reads the log files of the OVOS services. This page tells you how to cut a time slice, list the errors, shrink the files and print one log.

## Example

List the errors in `skills.log` after a start time:

```bash
ovos-logs list -e -s "2026-11-01 00:00" -l skills
```

```text
            skills (ERROR)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Time            ┃ Message ┃ Origin ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ 07:01:15.000 AM │ boom    │ x:y:2  │
└─────────────────┴─────────┴────────┘
```

The time column shows AM or PM when the `time_format` of ovos-config is `half`, and 24-hour time when it is `full`.

## Steps

1. Pick the command: `slice`, `list`, `reduce` or `show`.
2. Pick the logs with `-l`, once for each log: `-l bus -l skills`. With no `-l`, the command reads all logs in the default log directory.
3. Pick the time range with `-s` (start) and `-u` (until). Write the date as `YYYY-MM-DD`: an ambiguous date such as `01-11-2026` is read month first ([#477](https://github.com/OpenVoiceOS/ovos-utils/issues/477)). The start default is the last service start. The until default is the current time.
4. To read another directory, give `-p <dir>`. Also give `-l`: with `-p` and no `-l`, the command refuses the logs in that directory ([#476](https://github.com/OpenVoiceOS/ovos-utils/issues/476)).
5. To write the result to a file, give `-f <file>` (`slice` and `list`).

## Reference

| Command | Does | Options |
| :--- | :--- | :--- |
| `ovos-logs slice` | Writes the lines in a time range | `-s`, `-u`, `-l`, `-p`, `-f` |
| `ovos-logs list` | Lists the lines of one or more levels | `-e` error, `-w` warning, `-x` exception with traceback, `-d` debug; `-s`, `-u`, `-l`, `-p`, `-f` |
| `ovos-logs reduce` | Shrinks the logs to a size in bytes (`-s`), or removes the lines before a date (`-d`) | `-s`, `-d`, `-l`, `-p` |
| `ovos-logs show` | Prints one log | `-l` (required), `-p` |

`ovos-logs reduce` with no `-s` and no `-d` shrinks each log to 0 bytes. `ovos-logs <command> --help` prints all options.

---
[← Logging](log.md) · [Home](index.md) · [Next →](process-utils.md)
