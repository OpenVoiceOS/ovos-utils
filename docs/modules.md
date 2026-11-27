# Modules
<!-- agent-hint
covers: each module of ovos_utils and what it holds
source: ovos_utils/*.py, ovos_utils/lang/
generated: no
verify: python3 docs/check_page.py docs/modules.md && L=$(grep -o '^| `ovos_utils\.[a-z_]*`' docs/modules.md | grep -o '[a-z_]*`$' | tr -d '`' | sort); A=$( (ls ovos_utils/*.py | xargs -n1 basename | sed 's/\.py$//' | grep -v -e '^__init__$' -e '^version$'; echo lang) | sort); test "$L" = "$A"
see: fakebus.md
-->

This page lists each module of `ovos_utils` and what it holds. Import only the module that you need. The `verify` command of this page fails when a module is missing from the table, or when the table names a module that does not exist.

| Module | Holds |
| :--- | :--- |
| `ovos_utils.bracket_expansion` | Expansion of dialog templates such as `{a\|b}` and `(a\|b)` |
| `ovos_utils.decorators` | `classproperty` and `timed_lru_cache` |
| `ovos_utils.device_input` | `InputDeviceHelper`: is a touch screen, a mouse or a keyboard available |
| `ovos_utils.dialog` | `MustacheDialogRenderer`, `load_dialogs()`, `get_dialog()` and `join_list()` |
| `ovos_utils.events` | `EventContainer`, `EventSchedulerInterface` and handler wrappers. See [events.md](events.md). |
| `ovos_utils.fakebus` | `FakeBus`, `AsyncFakeBus` and `FakeMessage`. See [fakebus.md](fakebus.md). |
| `ovos_utils.file_utils` | Resource lookup, vocabulary loading and `FileWatcher`. See [utilities.md](utilities.md). |
| `ovos_utils.geolocation` | Time zone, geolocation and reverse geolocation lookups |
| `ovos_utils.gui` | Checks for an installed, running or connected GUI |
| `ovos_utils.json_helper` | JSON load and save helpers |
| `ovos_utils.lang` | `standardize_lang_tag()`, `get_language_dir()`, and phoneme and viseme helpers |
| `ovos_utils.list_utils` | `flatten_list()` and other list helpers |
| `ovos_utils.log` | `LOG`, `init_service_logger()` and `log_deprecation()`. See [log.md](log.md). |
| `ovos_utils.log_parser` | The parser behind the `ovos-logs` command. See [ovos-logs.md](ovos-logs.md). |
| `ovos_utils.messagebus` | Deprecated. Import from `ovos_utils.fakebus` or `ovos_bus_client`. |
| `ovos_utils.metrics` | `Stopwatch` and `LatencyHistogram`. See [metrics.md](metrics.md). |
| `ovos_utils.network_utils` | `get_ip()`, `is_connected_dns()`, `is_connected_http()` and `check_captive_portal()` |
| `ovos_utils.oauth` | OAuth token and application databases, and token refresh |
| `ovos_utils.ocp` | Media player (OCP) state enums, `MediaEntry`, `PluginStream` and `Playlist` |
| `ovos_utils.parse` | `fuzzy_match()`, `match_one()` and `match_all()` |
| `ovos_utils.process_utils` | `ProcessStatus`, `RuntimeRequirements`, `PIDLock` and `MonotonicEvent`. See [process-utils.md](process-utils.md). |
| `ovos_utils.prometheus` | The opt-in `/metrics` endpoint and the plugin collectors. See [metrics.md](metrics.md). |
| `ovos_utils.security` | Self-signed certificates, random keys, encryption and `sudo_exec()` |
| `ovos_utils.skill_installer` | `ServiceInstaller`: pip installs for a service |
| `ovos_utils.skills` | `skills_loaded()` and `get_non_properties()` |
| `ovos_utils.smtp_utils` | `send_email()` and `send_smtp()` |
| `ovos_utils.sound` | `play_audio()` and `get_sound_duration()` |
| `ovos_utils.ssml` | `SSMLBuilder` |
| `ovos_utils.system` | Service control, reboot, shutdown, SSH, and process and executable checks |
| `ovos_utils.text_utils` | `camel_case_split()`, `remove_accents_and_punct()` and other text helpers |
| `ovos_utils.thread_utils` | `create_daemon()`, `create_killable_daemon()`, `wait_for_exit_signal()` and `threaded_timeout` |
| `ovos_utils.time` | `now_local()`, `now_utc()`, `get_config_tz()` and time zone conversions |
| `ovos_utils.xdg_utils` | XDG base directory paths: `xdg_config_home()`, `xdg_data_home()` and others |
| `ovos_utils.xml_helper` | XML to dict and dict to XML |

## Environment variables

| Variable | Read by | Default | Effect |
| :--- | :--- | :--- | :--- |
| `OVOS_DEFAULT_LOG_NAME` | `LOG` | `OVOS` | The logger name |
| `OVOS_DEFAULT_LOG_LEVEL` | `LOG` | `INFO` | The log level |
| `OVOS_CONFIG_BASE_FOLDER` | `LOG`, `PIDLock` | `mycroft` | The XDG folder name |
| `OVOS_METRICS_ENABLED` | `ovos_utils.prometheus` | unset | Turns on the histograms and the endpoint |

---
[Home](index.md) · [Next →](fakebus.md)
