# Changelog

## [0.14.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.14.1a1) (2026-09-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.14.0a2...0.14.1a1)

**Merged pull requests:**

- fix: FakeBus stops folding the default session on every observed message [\#437](https://github.com/OpenVoiceOS/ovos-utils/pull/437) ([JarbasAl](https://github.com/JarbasAl))

## [0.14.0a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.14.0a2) (2026-09-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.14.0a1...0.14.0a2)

**Merged pull requests:**

- test: drop scheduler tests that pin ovos-bus-client internals [\#438](https://github.com/OpenVoiceOS/ovos-utils/pull/438) ([JarbasAl](https://github.com/JarbasAl))

## [0.14.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.14.0a1) (2026-09-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.15a1...0.14.0a1)

**Merged pull requests:**

- feat: FakeBus mirrors the .intent-suffixed twin for aliased intents [\#411](https://github.com/OpenVoiceOS/ovos-utils/pull/411) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.15a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.15a1) (2026-09-01)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.14a2...0.13.15a1)

**Merged pull requests:**

- fix: log\_deprecation checks its dedup set before walking the stack [\#433](https://github.com/OpenVoiceOS/ovos-utils/pull/433) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.14a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.14a2) (2026-08-31)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.14a1...0.13.14a2)

**Merged pull requests:**

- docs: add AGENTS.md with the conventions for coding agents [\#431](https://github.com/OpenVoiceOS/ovos-utils/pull/431) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.14a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.14a1) (2026-08-31)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.13a1...0.13.14a1)

**Merged pull requests:**

- fix: harden MediaEntry against invalid numeric fields and dict2entry error type [\#429](https://github.com/OpenVoiceOS/ovos-utils/pull/429) ([JarbasAl](https://github.com/JarbasAl))
- perf: skip disabled log call-site resolution [\#415](https://github.com/OpenVoiceOS/ovos-utils/pull/415) ([goldyfruit](https://github.com/goldyfruit))

## [0.13.13a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.13a1) (2026-08-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.12a2...0.13.13a1)

**Merged pull requests:**

- fix: floor ovos-spec-tools at the release that ships intent\_topics [\#427](https://github.com/OpenVoiceOS/ovos-utils/pull/427) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.12a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.12a2) (2026-08-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.12a1...0.13.12a2)

**Merged pull requests:**

- docs: add prerelease-quirks changelog since 0.8.5 [\#425](https://github.com/OpenVoiceOS/ovos-utils/pull/425) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.12a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.12a1) (2026-08-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.11a1...0.13.12a1)

**Merged pull requests:**

- fix: close leaked DNS-probe socket, silence deprecation warning noise [\#422](https://github.com/OpenVoiceOS/ovos-utils/pull/422) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.11a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.11a1) (2026-08-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.10a2...0.13.11a1)

**Merged pull requests:**

- fix: restore idempotent double-registration for intent-topic wrapped handlers [\#421](https://github.com/OpenVoiceOS/ovos-utils/pull/421) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.10a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.10a2) (2026-08-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.10a1...0.13.10a2)

**Merged pull requests:**

- docs\(fakebus\): clarify single-connection model for intent-topic bridge [\#419](https://github.com/OpenVoiceOS/ovos-utils/pull/419) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.10a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.10a1) (2026-08-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.9a2...0.13.10a1)

**Merged pull requests:**

- fix: give FakeBus the intent-topic bridge \(RULE 1/RULE 2 parity with MessageBusClient\) [\#417](https://github.com/OpenVoiceOS/ovos-utils/pull/417) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.9a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.9a2) (2026-08-01)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.9a1...0.13.9a2)

**Merged pull requests:**

- docs: rewrite README in Simplified Technical English [\#413](https://github.com/OpenVoiceOS/ovos-utils/pull/413) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.9a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.9a1) (2026-07-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.8a1...0.13.9a1)

**Merged pull requests:**

- fix: watch files that do not exist yet [\#408](https://github.com/OpenVoiceOS/ovos-utils/pull/408) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.8a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.8a1) (2026-07-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.7a2...0.13.8a1)

**Merged pull requests:**

- fix: FileEventHandler must only fire for the file it watches [\#406](https://github.com/OpenVoiceOS/ovos-utils/pull/406) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.7a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.7a2) (2026-07-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.7a1...0.13.7a2)

**Merged pull requests:**

- refactor: deprecate create\_self\_signed\_cert [\#404](https://github.com/OpenVoiceOS/ovos-utils/pull/404) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.7a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.7a1) (2026-07-23)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.6a1...0.13.7a1)

**Merged pull requests:**

- fix: replace removed distutils.spawn with shutil.which \(Python 3.12+\) [\#402](https://github.com/OpenVoiceOS/ovos-utils/pull/402) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.6a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.6a1) (2026-07-23)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.5a1...0.13.6a1)

**Merged pull requests:**

- fix: ovos-logs CLI leaves stray file in cwd [\#400](https://github.com/OpenVoiceOS/ovos-utils/pull/400) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.5a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.5a1) (2026-07-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.4a1...0.13.5a1)

**Merged pull requests:**

- fix: log each unique deprecation warning only once [\#398](https://github.com/OpenVoiceOS/ovos-utils/pull/398) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.4a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.4a1) (2026-07-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.3a1...0.13.4a1)

**Merged pull requests:**

- fix: FakeBus folds the message session BEFORE handlers, not after [\#396](https://github.com/OpenVoiceOS/ovos-utils/pull/396) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.3a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.3a1) (2026-06-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.2a1...0.13.3a1)

**Merged pull requests:**

- fix: FakeBus folds the default session like any other \(drop owner-only\) [\#393](https://github.com/OpenVoiceOS/ovos-utils/pull/393) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.2a1) (2026-06-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.1a1...0.13.2a1)

**Merged pull requests:**

- fix: drop deprecated make\_default from FakeBus default-session sync [\#389](https://github.com/OpenVoiceOS/ovos-utils/pull/389) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.1a1) (2026-06-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.13.0a1...0.13.1a1)

**Merged pull requests:**

- fix: target a real shape-changing pair in namespace-migration tests [\#390](https://github.com/OpenVoiceOS/ovos-utils/pull/390) ([JarbasAl](https://github.com/JarbasAl))

## [0.13.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.13.0a1) (2026-06-27)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.12.2a1...0.13.0a1)

**Merged pull requests:**

- feat: AsyncFakeBus namespace migration + env/config flag parity [\#387](https://github.com/OpenVoiceOS/ovos-utils/pull/387) ([JarbasAl](https://github.com/JarbasAl))

## [0.12.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.12.2a1) (2026-06-27)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.12.1a1...0.12.2a1)

**Merged pull requests:**

- fix: translate mirrored payload onto counterpart topic in FakeBus [\#385](https://github.com/OpenVoiceOS/ovos-utils/pull/385) ([JarbasAl](https://github.com/JarbasAl))

## [0.12.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.12.1a1) (2026-06-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.12.0a1...0.12.1a1)

**Merged pull requests:**

- fix: raise ovos-spec-tools floor to 0.10.0a1 for NamespaceTranslator [\#383](https://github.com/OpenVoiceOS/ovos-utils/pull/383) ([JarbasAl](https://github.com/JarbasAl))

## [0.12.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.12.0a1) (2026-06-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.11.2a1...0.12.0a1)

**Merged pull requests:**

- feat: FakeBus mirrors the legacy\<-\>ovos.\* namespace migration [\#381](https://github.com/OpenVoiceOS/ovos-utils/pull/381) ([JarbasAl](https://github.com/JarbasAl))

## [0.11.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.11.2a1) (2026-06-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.11.1a1...0.11.2a1)

**Merged pull requests:**

- fix: allow json-database 1.x [\#379](https://github.com/OpenVoiceOS/ovos-utils/pull/379) ([JarbasAl](https://github.com/JarbasAl))

## [0.11.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.11.1a1) (2026-05-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.11.0a1...0.11.1a1)

**Merged pull requests:**

- fix: standardize\_lang\_tag macro=True preserves region \(restore langcodes semantics\) [\#377](https://github.com/OpenVoiceOS/ovos-utils/pull/377) ([JarbasAl](https://github.com/JarbasAl))

## [0.11.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.11.0a1) (2026-05-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.10.0a1...0.11.0a1)

**Merged pull requests:**

- feat: fakebus Message subclasses ovos\_spec\_tools.Message — no API break [\#375](https://github.com/OpenVoiceOS/ovos-utils/pull/375) ([JarbasAl](https://github.com/JarbasAl))

## [0.10.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.10.0a1) (2026-05-22)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.9.0a1...0.10.0a1)

**Merged pull requests:**

- feat: migrate ovos-utils onto ovos-spec-tools [\#373](https://github.com/OpenVoiceOS/ovos-utils/pull/373) ([JarbasAl](https://github.com/JarbasAl))

## [0.9.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.9.0a1) (2026-05-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.5...0.9.0a1)

**Merged pull requests:**

- feat: AsyncFakeBus alongside FakeBus [\#371](https://github.com/OpenVoiceOS/ovos-utils/pull/371) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.5](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.5) (2026-03-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.5a4...0.8.5)

## [0.8.5a4](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.5a4) (2026-03-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.6a2...0.8.5a4)

**Merged pull requests:**

- chore: Add comprehensive test suites and documentation [\#362](https://github.com/OpenVoiceOS/ovos-utils/pull/362) ([JarbasAl](https://github.com/JarbasAl))
- fix: make the stopwatch test less strict [\#360](https://github.com/OpenVoiceOS/ovos-utils/pull/360) ([PureTryOut](https://github.com/PureTryOut))

## [0.8.6a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.6a2) (2026-02-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.6a1...0.8.6a2)

**Merged pull requests:**

- chore\(deps\): update actions/setup-python action to v6 [\#353](https://github.com/OpenVoiceOS/ovos-utils/pull/353) ([renovate[bot]](https://github.com/apps/renovate))
- chore\(deps\): update actions/checkout action to v6 [\#352](https://github.com/OpenVoiceOS/ovos-utils/pull/352) ([renovate[bot]](https://github.com/apps/renovate))

## [0.8.6a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.6a1) (2026-02-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.5a3...0.8.6a1)

**Merged pull requests:**

- fix: prevent handler errors from aborting FakeBus emit [\#358](https://github.com/OpenVoiceOS/ovos-utils/pull/358) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.5a3](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.5a3) (2025-12-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.5a2...0.8.5a3)

**Merged pull requests:**

- chore\(deps\): update dependency python to 3.14 [\#348](https://github.com/OpenVoiceOS/ovos-utils/pull/348) ([renovate[bot]](https://github.com/apps/renovate))

## [0.8.5a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.5a2) (2025-12-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.5a1...0.8.5a2)

**Merged pull requests:**

- Release 0.8.5a2 [\#351](https://github.com/OpenVoiceOS/ovos-utils/pull/351) ([github-actions[bot]](https://github.com/apps/github-actions))
- chore: Configure Renovate [\#347](https://github.com/OpenVoiceOS/ovos-utils/pull/347) ([renovate[bot]](https://github.com/apps/renovate))

## [0.8.5a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.5a1) (2025-11-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.4...0.8.5a1)

**Merged pull requests:**

- Release 0.8.5a1 [\#344](https://github.com/OpenVoiceOS/ovos-utils/pull/344) ([github-actions[bot]](https://github.com/apps/github-actions))
- fix: use timezone-aware datetime functions and update scheduler event names [\#343](https://github.com/OpenVoiceOS/ovos-utils/pull/343) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.4](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.4) (2025-11-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.4a1...0.8.4)

## [0.8.4a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.4a1) (2025-10-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.3a1...0.8.4a1)

**Merged pull requests:**

- fix: handle issues in NVDA python stdlib [\#341](https://github.com/OpenVoiceOS/ovos-utils/pull/341) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.3a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.3a1) (2025-10-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.2a1...0.8.3a1)

**Merged pull requests:**

- fix: fail safe when used in applications with conflicting watchdog  [\#338](https://github.com/OpenVoiceOS/ovos-utils/pull/338) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.2a1) (2025-09-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.1...0.8.2a1)

**Merged pull requests:**

- fix: make orjson optional [\#335](https://github.com/OpenVoiceOS/ovos-utils/pull/335) ([JarbasAl](https://github.com/JarbasAl))

## [0.8.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.1) (2025-06-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.0a2...0.8.1)

**Merged pull requests:**

- Release 0.8.0a2 [\#332](https://github.com/OpenVoiceOS/ovos-utils/pull/332) ([github-actions[bot]](https://github.com/apps/github-actions))

## [0.8.0a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.0a2) (2025-06-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.0...0.8.0a2)

## [0.8.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.0) (2025-06-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.8.0a1...0.8.0)

## [0.8.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.8.0a1) (2025-05-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.7.1...0.8.0a1)

## [0.7.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.7.1) (2025-04-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.7.1a1...0.7.1)

## [0.7.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.7.1a1) (2025-04-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.7.0...0.7.1a1)

## [0.7.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.7.0) (2025-02-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.7.0a1...0.7.0)

## [0.7.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.7.0a1) (2025-02-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.6.1...0.7.0a1)

## [0.6.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.6.1) (2025-01-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.6.1a2...0.6.1)

## [0.6.1a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.6.1a2) (2025-01-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.6.1a1...0.6.1a2)

## [0.6.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.6.1a1) (2025-01-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.6.0...0.6.1a1)

## [0.6.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.6.0) (2024-12-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.6.0a1...0.6.0)

## [0.6.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.6.0a1) (2024-12-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.6...0.6.0a1)

## [0.5.6](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.6) (2024-12-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.6a1...0.5.6)

## [0.5.6a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.6a1) (2024-12-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.5...0.5.6a1)

## [0.5.5](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.5) (2024-11-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.5a1...0.5.5)

## [0.5.5a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.5a1) (2024-11-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.4...0.5.5a1)

## [0.5.4](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.4) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.4a1...0.5.4)

## [0.5.4a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.4a1) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.3...0.5.4a1)

## [0.5.3](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.3) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.3a1...0.5.3)

## [0.5.3a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.3a1) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.2...0.5.3a1)

## [0.5.2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.2) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.2a1...0.5.2)

## [0.5.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.2a1) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.1...0.5.2a1)

## [0.5.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.1) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.1a1...0.5.1)

## [0.5.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.1a1) (2024-11-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.0...0.5.1a1)

## [0.5.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.0) (2024-11-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.5.0a1...0.5.0)

## [0.5.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.5.0a1) (2024-11-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.4.1...0.5.0a1)

## [0.4.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.4.1) (2024-11-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.4.1a1...0.4.1)

## [0.4.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.4.1a1) (2024-11-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.4.0...0.4.1a1)

## [0.4.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.4.0) (2024-11-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.8a2...0.4.0)

## [0.3.8a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.8a2) (2024-11-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.8a1...0.3.8a2)

## [0.3.8a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.8a1) (2024-11-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.7...0.3.8a1)

## [0.3.7](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.7) (2024-11-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.7a1...0.3.7)

## [0.3.7a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.7a1) (2024-11-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.6...0.3.7a1)

## [0.3.6](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.6) (2024-10-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.6a1...0.3.6)

## [0.3.6a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.6a1) (2024-10-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.5...0.3.6a1)

## [0.3.5](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.5) (2024-10-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.5a1...0.3.5)

## [0.3.5a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.5a1) (2024-10-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.4...0.3.5a1)

## [0.3.4](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.4) (2024-10-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.4a1...0.3.4)

## [0.3.4a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.4a1) (2024-10-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.3...0.3.4a1)

## [0.3.3](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.3) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.3a1...0.3.3)

## [0.3.3a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.3a1) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.2a1...0.3.3a1)

## [0.3.2a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.2a1) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.1...0.3.2a1)

## [0.3.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.1) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.1a2...0.3.1)

## [0.3.1a2](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.1a2) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.1a1...0.3.1a2)

## [0.3.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.1a1) (2024-10-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.0...0.3.1a1)

## [0.3.0](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.0) (2024-10-09)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.3.0a1...0.3.0)

## [0.3.0a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.3.0a1) (2024-09-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.2.1...0.3.0a1)

## [0.2.1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.2.1) (2024-09-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.2.1a1...0.2.1)

## [0.2.1a1](https://github.com/OpenVoiceOS/ovos-utils/tree/0.2.1a1) (2024-09-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.1.0...0.2.1a1)

## [V0.1.0](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.1.0) (2024-09-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.38...V0.1.0)

## [V0.0.38](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.38) (2023-12-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.37.post1...V0.0.38)

## [V0.0.37.post1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.37.post1) (2023-12-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0."37.post1"...V0.0.37.post1)

## [V0.0."37.post1"](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0."37.post1") (2023-12-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.37...V0.0."37.post1")

## [V0.0.37](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.37) (2023-12-28)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.37a2...V0.0.37)

## [V0.0.37a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.37a2) (2023-12-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.37a1...V0.0.37a2)

## [V0.0.37a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.37a1) (2023-11-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36...V0.0.37a1)

## [V0.0.36](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36) (2023-10-26)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a12...V0.0.36)

## [V0.0.36a12](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a12) (2023-10-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a11...V0.0.36a12)

## [V0.0.36a11](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a11) (2023-10-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a10...V0.0.36a11)

## [V0.0.36a10](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a10) (2023-10-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a9...V0.0.36a10)

## [V0.0.36a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a9) (2023-10-12)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a8...V0.0.36a9)

## [V0.0.36a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a8) (2023-09-26)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a7...V0.0.36a8)

## [V0.0.36a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a7) (2023-09-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a6...V0.0.36a7)

## [V0.0.36a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a6) (2023-09-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a5...V0.0.36a6)

## [V0.0.36a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a5) (2023-09-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a4...V0.0.36a5)

## [V0.0.36a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a4) (2023-09-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a3...V0.0.36a4)

## [V0.0.36a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a3) (2023-08-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a2...V0.0.36a3)

## [V0.0.36a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a2) (2023-08-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.36a1...V0.0.36a2)

## [V0.0.36a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.36a1) (2023-08-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35...V0.0.36a1)

## [V0.0.35](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35) (2023-07-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a9...V0.0.35)

## [V0.0.35a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a9) (2023-07-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a8...V0.0.35a9)

## [V0.0.35a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a8) (2023-07-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a7...V0.0.35a8)

## [V0.0.35a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a7) (2023-07-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a6...V0.0.35a7)

## [V0.0.35a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a6) (2023-07-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a5...V0.0.35a6)

## [V0.0.35a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a5) (2023-07-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a4...V0.0.35a5)

## [V0.0.35a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a4) (2023-07-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a3...V0.0.35a4)

## [V0.0.35a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a3) (2023-07-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a2...V0.0.35a3)

## [V0.0.35a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a2) (2023-06-28)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.35a1...V0.0.35a2)

## [V0.0.35a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.35a1) (2023-06-21)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34...V0.0.35a1)

## [V0.0.34](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34) (2023-06-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a9...V0.0.34)

## [V0.0.34a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a9) (2023-06-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a8...V0.0.34a9)

## [V0.0.34a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a8) (2023-06-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a7...V0.0.34a8)

## [V0.0.34a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a7) (2023-06-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a6...V0.0.34a7)

## [V0.0.34a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a6) (2023-06-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a5...V0.0.34a6)

## [V0.0.34a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a5) (2023-06-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a3...V0.0.34a5)

## [V0.0.34a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a3) (2023-06-09)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a2...V0.0.34a3)

## [V0.0.34a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a2) (2023-06-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.34a1...V0.0.34a2)

## [V0.0.34a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.34a1) (2023-06-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33...V0.0.34a1)

## [V0.0.33](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33) (2023-06-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a12...V0.0.33)

## [V0.0.33a12](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a12) (2023-05-31)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a11...V0.0.33a12)

## [V0.0.33a11](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a11) (2023-05-30)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a10...V0.0.33a11)

## [V0.0.33a10](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a10) (2023-05-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a9...V0.0.33a10)

## [V0.0.33a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a9) (2023-05-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a8...V0.0.33a9)

## [V0.0.33a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a8) (2023-05-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a7...V0.0.33a8)

## [V0.0.33a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a7) (2023-05-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a6...V0.0.33a7)

## [V0.0.33a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a6) (2023-05-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a5...V0.0.33a6)

## [V0.0.33a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a5) (2023-05-01)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a4...V0.0.33a5)

## [V0.0.33a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a4) (2023-05-01)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a3...V0.0.33a4)

## [V0.0.33a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a3) (2023-04-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a2...V0.0.33a3)

## [V0.0.33a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a2) (2023-04-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.33a1...V0.0.33a2)

## [V0.0.33a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.33a1) (2023-04-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.32...V0.0.33a1)

## [V0.0.32](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.32) (2023-04-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a18...V0.0.32)

## [V0.0.31a18](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a18) (2023-04-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a17...V0.0.31a18)

## [V0.0.31a17](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a17) (2023-04-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a16...V0.0.31a17)

## [V0.0.31a16](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a16) (2023-04-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a15...V0.0.31a16)

## [V0.0.31a15](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a15) (2023-04-14)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a14...V0.0.31a15)

## [V0.0.31a14](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a14) (2023-04-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a13...V0.0.31a14)

## [V0.0.31a13](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a13) (2023-04-13)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a12...V0.0.31a13)

## [V0.0.31a12](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a12) (2023-04-12)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a11...V0.0.31a12)

## [V0.0.31a11](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a11) (2023-04-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a10...V0.0.31a11)

## [V0.0.31a10](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a10) (2023-04-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a9...V0.0.31a10)

## [V0.0.31a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a9) (2023-04-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a8...V0.0.31a9)

## [V0.0.31a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a8) (2023-04-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a7...V0.0.31a8)

## [V0.0.31a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a7) (2023-04-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a6...V0.0.31a7)

## [V0.0.31a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a6) (2023-04-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a5...V0.0.31a6)

## [V0.0.31a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a5) (2023-04-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a4...V0.0.31a5)

## [V0.0.31a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a4) (2023-04-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a3...V0.0.31a4)

## [V0.0.31a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a3) (2023-04-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a2...V0.0.31a3)

## [V0.0.31a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a2) (2023-04-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.31a1...V0.0.31a2)

## [V0.0.31a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.31a1) (2023-03-23)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.30...V0.0.31a1)

## [V0.0.30](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.30) (2023-03-09)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.30a4...V0.0.30)

## [V0.0.30a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.30a4) (2023-03-09)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.30a3...V0.0.30a4)

## [V0.0.30a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.30a3) (2023-03-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.30a2...V0.0.30a3)

## [V0.0.30a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.30a2) (2023-03-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.30a1...V0.0.30a2)

## [V0.0.30a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.30a1) (2023-03-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.29...V0.0.30a1)

## [V0.0.29](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.29) (2023-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.29a2...V0.0.29)

## [V0.0.29a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.29a2) (2023-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.29a1...V0.0.29a2)

## [V0.0.29a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.29a1) (2023-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28...V0.0.29a1)

## [V0.0.28](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28) (2023-02-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a7...V0.0.28)

## [V0.0.28a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a7) (2023-02-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a6...V0.0.28a7)

## [V0.0.28a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a6) (2023-02-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a5...V0.0.28a6)

## [V0.0.28a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a5) (2023-02-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a4...V0.0.28a5)

## [V0.0.28a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a4) (2023-02-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a3...V0.0.28a4)

## [V0.0.28a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a3) (2023-02-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a2...V0.0.28a3)

## [V0.0.28a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a2) (2023-02-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.28a1...V0.0.28a2)

## [V0.0.28a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.28a1) (2023-01-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27...V0.0.28a1)

## [V0.0.27](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27) (2023-01-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a8...V0.0.27)

## [V0.0.27a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a8) (2023-01-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a7...V0.0.27a8)

## [V0.0.27a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a7) (2023-01-12)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a6...V0.0.27a7)

## [V0.0.27a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a6) (2023-01-05)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a5...V0.0.27a6)

## [V0.0.27a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a5) (2022-12-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a4...V0.0.27a5)

## [V0.0.27a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a4) (2022-11-30)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a3...V0.0.27a4)

## [V0.0.27a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a3) (2022-11-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a2...V0.0.27a3)

## [V0.0.27a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a2) (2022-11-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.27a1...V0.0.27a2)

## [V0.0.27a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.27a1) (2022-11-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.26...V0.0.27a1)

## [V0.0.26](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.26) (2022-10-29)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.26a2...V0.0.26)

## [V0.0.26a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.26a2) (2022-10-22)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.26a1...V0.0.26a2)

## [V0.0.26a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.26a1) (2022-10-19)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25...V0.0.26a1)

## [V0.0.25](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25) (2022-10-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a15...V0.0.25)

## [V0.0.25a15](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a15) (2022-10-18)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a14...V0.0.25a15)

## [V0.0.25a14](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a14) (2022-10-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a13...V0.0.25a14)

## [V0.0.25a13](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a13) (2022-10-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a12...V0.0.25a13)

## [V0.0.25a12](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a12) (2022-10-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a11...V0.0.25a12)

## [V0.0.25a11](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a11) (2022-10-11)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a10...V0.0.25a11)

## [V0.0.25a10](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a10) (2022-10-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a9...V0.0.25a10)

## [V0.0.25a9](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a9) (2022-10-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a8...V0.0.25a9)

## [V0.0.25a8](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a8) (2022-10-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a7...V0.0.25a8)

## [V0.0.25a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a7) (2022-10-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a6...V0.0.25a7)

## [V0.0.25a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a6) (2022-09-28)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a5...V0.0.25a6)

## [V0.0.25a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a5) (2022-09-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a4...V0.0.25a5)

## [V0.0.25a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a4) (2022-09-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a3...V0.0.25a4)

## [V0.0.25a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a3) (2022-09-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a2...V0.0.25a3)

## [V0.0.25a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a2) (2022-09-08)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.25a1...V0.0.25a2)

## [V0.0.25a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.25a1) (2022-09-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.24...V0.0.25a1)

## [V0.0.24](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.24) (2022-09-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.24a4...V0.0.24)

## [V0.0.24a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.24a4) (2022-09-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.24a3...V0.0.24a4)

## [V0.0.24a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.24a3) (2022-09-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.24a2...V0.0.24a3)

## [V0.0.24a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.24a2) (2022-08-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.24a1...V0.0.24a2)

## [V0.0.24a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.24a1) (2022-08-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23...V0.0.24a1)

## [V0.0.23](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23) (2022-07-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a7...V0.0.23)

## [V0.0.23a7](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a7) (2022-07-20)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a6...V0.0.23a7)

## [V0.0.23a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a6) (2022-07-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a5...V0.0.23a6)

## [V0.0.23a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a5) (2022-07-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a4...V0.0.23a5)

## [V0.0.23a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a4) (2022-07-06)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a3...V0.0.23a4)

## [V0.0.23a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a3) (2022-06-15)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a2...V0.0.23a3)

## [V0.0.23a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a2) (2022-06-10)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.23a1...V0.0.23a2)

## [V0.0.23a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.23a1) (2022-06-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.22...V0.0.23a1)

## [V0.0.22](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.22) (2022-06-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.22a3...V0.0.22)

## [V0.0.22a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.22a3) (2022-06-02)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.22a2...V0.0.22a3)

## [V0.0.22a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.22a2) (2022-05-31)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.22a1...V0.0.22a2)

## [V0.0.22a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.22a1) (2022-05-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21...V0.0.22a1)

## [V0.0.21](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21) (2022-05-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a6...V0.0.21)

## [V0.0.21a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a6) (2022-05-17)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a5...V0.0.21a6)

## [V0.0.21a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a5) (2022-05-12)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a4...V0.0.21a5)

## [V0.0.21a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a4) (2022-05-09)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a3...V0.0.21a4)

## [V0.0.21a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a3) (2022-05-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a2...V0.0.21a3)

## [V0.0.21a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a2) (2022-05-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.21a1...V0.0.21a2)

## [V0.0.21a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.21a1) (2022-05-07)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.20...V0.0.21a1)

## [V0.0.20](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.20) (2022-04-27)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.20a4...V0.0.20)

## [V0.0.20a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.20a4) (2022-04-27)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.20a3...V0.0.20a4)

## [V0.0.20a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.20a3) (2022-03-23)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.20a2...V0.0.20a3)

## [V0.0.20a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.20a2) (2022-03-16)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.20a1...V0.0.20a2)

## [V0.0.20a1](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.20a1) (2022-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.19...V0.0.20a1)

## [V0.0.19](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.19) (2022-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.19a3...V0.0.19)

## [V0.0.19a3](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.19a3) (2022-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.19a2...V0.0.19a3)

## [V0.0.19a2](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.19a2) (2022-03-03)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.17a6...V0.0.19a2)

## [V0.0.17a6](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.17a6) (2022-02-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.17a5...V0.0.17a6)

## [V0.0.17a5](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.17a5) (2022-02-25)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.18...V0.0.17a5)

## [V0.0.18](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.18) (2022-02-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/V0.0.17a4...V0.0.18)

## [V0.0.17a4](https://github.com/OpenVoiceOS/ovos-utils/tree/V0.0.17a4) (2022-02-24)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/0.0.12...V0.0.17a4)

## [0.0.12](https://github.com/OpenVoiceOS/ovos-utils/tree/0.0.12) (2021-11-04)

[Full Changelog](https://github.com/OpenVoiceOS/ovos-utils/compare/25fe462e3c19a58f32dc1fd940bf7c96fc18e6de...0.0.12)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
