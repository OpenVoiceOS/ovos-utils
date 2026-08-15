# Prerelease quirks

This page tracks user-visible behavior changes since the last stable release,
`0.8.5`. The alpha train has run a long time without a stable cut, so this
list spans `0.9.0a1` through the current HEAD. Newest first. This file resets
to empty at the next stable release.

## next alpha

- The `ovos-spec-tools` floor moves to `>=1.6.0a2`, the first release whose
  `intent_topics` module has the shape `ovos_utils.fakebus` imports. The old
  floor (`>=0.16.1a2`) was satisfied numerically by releases without the
  module at all, which made ovos-utils unimportable in resolved-but-stale
  environments — only a real install caught it.


## 0.13.12a1 — closed a leaked DNS-probe socket

`is_connected_dns()` opened a raw socket for its reachability probe and never
closed it. Every call, and every failed probe (the common case on a flaky
network), leaked a file descriptor. The socket now closes in a `finally`
block. Return semantics are unchanged.

## 0.13.11a1 — `FakeBus.once()` re-registration is idempotent again

Re-registering the same `(msg_type, handler)` pair on `FakeBus.on()` or
`once()` used to collapse onto one listener slot, matching how `pyee` keys
listeners by handler object. A later change minted a fresh wrapper closure on
every call, so `pyee` saw a new object each time and fired the handler twice.
Both `on()` and `once()` now reuse the existing wrapper for a given
`(msg_type, handler)` pair, restoring one-fire-per-registration behavior.

## 0.13.10a1 / 0.13.10a2 — `FakeBus` gained the intent-topic bridge

`FakeBus` now mirrors `MessageBusClient`'s canonical `<-> .intent`-suffixed
topic bridge (RULE 1 / RULE 2), so tests against `FakeBus` see the same
dual-spelling delivery a real bus connection gives them.

Capture semantics you should know before writing tests against it:

- `FakeBus` models **one bus connection**. Within that connection, an
  intent-topic pair shares one dedup guard, so if both spellings have
  subscribers, only the spelling actually emitted (or its canonical
  modernization) is delivered — same as sharing one real client connection.
  A legacy-only listener starves on a canonical emit. This is not a bug.
- The twin/modernized frame dispatched by the bridge does **not** re-fire the
  `"message"` firehose a second time. On a real wire the twin is a second
  frame and does trigger `on_message` (and `"message"`) again in every
  receiving process. `FakeBus` has no wire hop to put that second frame on,
  so it keeps a single-process, one-emit-one-capture invariant instead.
  Test authors who subscribe to `"message"` to capture everything a skill
  emits will not see the mirrored twin as a separate capture — subscribe to
  the canonical topic itself if the twin matters to the assertion.
- `FakeBus` cannot represent multiple bus **connections**. An external
  observer attached to the same `FakeBus` as the code under test shares its
  dedup guard instead of running an independent one, unlike two real
  connections on the wire.

## 0.13.9a1 — `FileEventHandler` fires only for its own file; watches files that don't exist yet

Two related fixes: a `FileEventHandler` no longer fires for changes to other
files under watch, and `FileWatcher` can now be pointed at a path that does
not exist yet (it starts watching once created instead of failing).

## 0.13.8a1 — `distutils.spawn` replaced with `shutil.which`

`distutils` is removed in Python 3.12+. Any code path that depended on
`ovos-utils` transitively importing `distutils.spawn` now uses `shutil.which`.

## 0.13.0a1 – 0.13.x — namespace-migration bridge, `AsyncFakeBus`, `ovos-spec-tools` adoption

This stretch of the alpha train reworked the bus-testing surface:

- `AsyncFakeBus` was added alongside `FakeBus` as an async-native counterpart.
- `fakebus.Message` now subclasses `ovos_spec_tools.Message` — no API break,
  but `ovos-utils` now depends on `ovos-spec-tools` (floor raised to
  `0.10.0a1` for `NamespaceTranslator`).
- `FakeBus`/`AsyncFakeBus` mirror the legacy `<-> ovos.*` namespace migration:
  emitting on either spelling of a migrated topic dispatches the counterpart
  too, with the payload reshaped into the counterpart's shape where the
  migration changed it. The default session is folded into the message
  context before handlers run, matching `MessageBusClient.on_message`'s
  receive-then-fold-then-dispatch order (folding after handlers would wipe
  in-place session mutations a handler made).
- `standardize_lang_tag(macro=True)` again preserves region, restoring the
  original `langcodes` semantics.
- `json-database` 1.x is now an allowed dependency floor.

## Known nondeterminism / preexisting quirks

- The DNS-probe file-descriptor leak above is fixed; a `ResourceWarning`
  sourced from the still-installed, unpatched `ovos-bus-client` dependency's
  own `session.py` can still appear until that fix ships upstream — it does
  not originate in this repo.

See [docs/fakebus.md](fakebus.md) for the full `FakeBus`/`AsyncFakeBus`
reference, including the intent-topic bridge and namespace-migration bridge
in detail.
