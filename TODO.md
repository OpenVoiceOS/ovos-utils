# TODO — ovos-utils

## Open issues

- [ ] #350 Dependency Dashboard
- [ ] #318 Improve error handling when all template lines fail to expand
- [ ] #297 Security Concern: Consider using a geolocation service that supports HTTPS
- [ ] #261 ovos-logs TypeError in log_parser.py ~372
- [ ] #250 after a day running in debug mode I get an error
- [ ] #245 pipewire audio ducking
- [ ] #241 ocp.py - These should be moved into unit tests
- [ ] #238 log_parser.py - New module missing test coverage
- [ ] #233 ovos-logs tail
- [ ] #228 ovos-logs feature request
- [ ] #227 ovos-logs slice fails
- [ ] #226 Dependabot does not install the extras extra
- [ ] #217 OCP util unittests
- [ ] #172 EventContainer scope event removal
- [ ] #155 Implement shared action for CodeCov
- [ ] #108 rework of `FileEventHandler` to handle content change below given path

## Gaps

- [ ] Committed packaging artifact: `ovos_utils.egg-info/` is tracked in the repo and should be gitignored.
- [ ] Stray empty scratch file `ovos_logs_console_script` at repo root.
- [ ] Stray non-standard root docs: `MAINTENANCE_REPORT.md`, `QUICK_FACTS.md`, `FAQ.md`, `downstream_report.txt` — clutter; fold into `docs/` or remove.
- [ ] README still says "collection of simple utilities for use across the mycroft ecosystem" — should reference OpenVoiceOS.
- [ ] `[project.urls]` Homepage/Repository point at `github.com/OpenVoiceOS/ovos_utils` (underscore) instead of the actual slug `OpenVoiceOS/ovos-utils`.
- [ ] CI present and standard (build-tests, coverage, license_check, lint, pip_audit, release_workflow/publish-alpha, publish_stable, release-preview, repo-health all reference gh-automations `@dev`). No `opm-check`/`skill-check` needed — not a plugin/skill.

## Code TODOs

- ovos_utils/security.py:60 — `# TODO don't use sha1`
- ovos_utils/file_utils.py:149 — `# TODO - remove me soon, spams deprecation logs`
- ovos_utils/dialog.py:32 — `# TODO magic numbers are bad!`
- ovos_utils/events.py:252 — `# TODO: Is a null name valid or should it raise an exception?`
- ovos_utils/log_parser.py:170 — `# TODO do tracebacks always end on a empty line?`
- ovos_utils/parse.py:116 — `# TODO solve ties`
- ovos_utils/process_utils.py:355 — `# TODO - make it work in windows ?`
- ovos_utils/geolocation.py:114,127 — lang support / country-code-to-name
- ovos_utils/ocp.py:152,337 — dead symbol kept for downstream import; deprecation path
