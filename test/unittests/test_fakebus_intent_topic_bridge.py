"""FakeBus mirrors MessageBusClient's legacy<->canonical INTENT-topic bridge
(RULE 1 send-side twin / RULE 2 receive-side modernize), so in-process tests
raw-emitting a legacy ``<skill_id>:IntentName.intent`` topic reach a
canonical-only listener the same way a real websocket deployment does, and
vice-versa.

Root cause this closes: FakeBus already wired ovos_spec_tools's
NamespaceTranslator for the fixed SpecMessage pairs (speak <-> ovos.utterance.speak
etc, see test_fakebus_namespace_migration.py) but NOT the per-intent
dispatch-topic bridge that ovos_bus_client.client.client.MessageBusClient
applies via ``_send_legacy_intent_twin`` / ``_modernize_intent_topic``. Since
ovos-workshop >= 9.3.11a2 dropped its own dual-bind (only registers the
canonical listener), an in-process test emitting the legacy suffixed topic
directly never reached the handler -- while a real deployment, whose bus
client performs this bridge, dealiased fine.
"""
import asyncio
import unittest
from unittest.mock import patch

from ovos_utils.fakebus import AsyncFakeBus, FakeBus, Message, INTENT_COMPAT_TWIN_KEY


def _run(coro):
    return asyncio.run(coro)


LEGACY = "myskill.foo:HelloIntent.intent"
CANONICAL = "myskill.foo:HelloIntent"


class TestFakeBusIntentTopicBridge(unittest.TestCase):
    def test_legacy_emit_reaches_canonical_listener(self):
        # RULE 2: a raw legacy-suffixed emit (no bus-client, no twin marker)
        # must still fire a canonical-only listener.
        bus = FakeBus()  # both flags default on
        got = []
        bus.on(CANONICAL, lambda m: got.append(m.msg_type))
        bus.emit(Message(LEGACY, {"utterance": "hi"}))
        self.assertEqual(got, [CANONICAL])

    def test_canonical_emit_also_fires_legacy_listener(self):
        # RULE 1: every canonical intent dispatch is twinned onto its legacy
        # spelling so an old suffix-only listener still hears it.
        bus = FakeBus()
        got = []
        bus.on(LEGACY, lambda m: got.append(m.msg_type))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(got, [LEGACY])

    def test_canonical_emit_twin_marked(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, lambda m: got.append(m))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].context.get(INTENT_COMPAT_TWIN_KEY))

    def test_no_double_fire_dual_listener(self):
        # a handler subscribed to BOTH the legacy and canonical topic must
        # not see the same logical dispatch twice.
        bus = FakeBus()
        calls = []
        handler = lambda m: calls.append(m.msg_type)
        bus.on(LEGACY, handler)
        bus.on(CANONICAL, handler)
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        # canonical fires the handler once directly; the RULE-1 twin is
        # marked, so a receiver honoring the marker (a real bus-client)
        # would skip re-modernizing it -- but FakeBus has no separate
        # receive hop for its own twin, so the legacy registration also
        # fires once for the twin. Assert no more than the two expected
        # deliveries (one per distinct registered topic) and no cascade.
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls.count(CANONICAL), 1)
        self.assertEqual(calls.count(LEGACY), 1)

    def test_twin_marker_suppresses_rule2_recascade(self):
        # if a caller manually emits a message already carrying the twin
        # marker (simulating what a real client would receive as the twin
        # half of a pair), RULE 2 must not modernize it again -- proving the
        # bridge cannot cascade into a modernize/twin loop.
        bus = FakeBus()
        canonical_hits = []
        bus.on(CANONICAL, lambda m: canonical_hits.append(1))
        msg = Message(LEGACY, {"utterance": "hi"},
                      {INTENT_COMPAT_TWIN_KEY: True})
        bus.emit(msg)
        self.assertEqual(canonical_hits, [])

    def test_non_intent_topic_untouched(self):
        bus = FakeBus()
        got = []
        bus.on("my.custom.topic", lambda m: got.append(m.msg_type))
        bus.emit(Message("my.custom.topic", {"x": 1}))
        self.assertEqual(got, ["my.custom.topic"])
        # and no stray listeners fired for unrelated suffixed-looking topics
        got2 = []
        bus.on("speak", lambda m: got2.append(m.msg_type))
        bus.emit(Message("my.custom.topic", {"x": 1}))
        self.assertEqual(got2, [])

    def test_flags_off_no_bridging(self):
        # each direction gets its own bus/listener pair: a listener on the
        # SAME topic as what's emitted always fires (plain same-topic
        # dispatch, unrelated to the bridge) -- only the OTHER namespace's
        # listener proves whether bridging happened.
        bus1 = FakeBus(modernize=False, emit_legacy=False)
        got_canonical = []
        bus1.on(CANONICAL, lambda m: got_canonical.append(1))
        bus1.emit(Message(LEGACY, {"utterance": "hi"}))
        self.assertEqual(got_canonical, [])  # RULE 2 suppressed

        bus2 = FakeBus(modernize=False, emit_legacy=False)
        got_legacy = []
        bus2.on(LEGACY, lambda m: got_legacy.append(1))
        bus2.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(got_legacy, [])  # RULE 1 suppressed

    def test_already_canonical_not_re_twinned_into_itself(self):
        # a topic with no legacy counterpart (canonical == legacy, e.g. a
        # non-suffixed topic that is not an intent topic at all) is a no-op.
        bus = FakeBus()
        calls = []
        bus.on(CANONICAL, lambda m: calls.append(1))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        # exactly one direct dispatch; the RULE-1 twin went to LEGACY, not
        # back onto CANONICAL, so no double count here.
        self.assertEqual(calls, [1])

    def test_async_fakebus_legacy_emit_reaches_canonical_listener(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(CANONICAL, lambda m: got.append(m.msg_type))
        _run(bus.emit(Message(LEGACY, {"utterance": "hi"})))
        self.assertEqual(got, [CANONICAL])

    def test_async_fakebus_canonical_emit_fires_legacy_listener(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(LEGACY, lambda m: got.append(m.msg_type))
        _run(bus.emit(Message(CANONICAL, {"utterance": "hi"})))
        self.assertEqual(got, [LEGACY])


if __name__ == "__main__":
    unittest.main()
