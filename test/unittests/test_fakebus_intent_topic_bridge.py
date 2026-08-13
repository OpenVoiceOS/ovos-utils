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

    def test_canonical_emit_twin_not_marked_locally(self):
        # On the real wire the RULE-1 twin goes out MARKED so an
        # out-of-process receiver's RULE 2 knows to skip re-modernizing it.
        # FakeBus has no wire hop: it already made that RULE-2 call inline
        # for this dispatch, so the twin delivered to LOCAL listeners must
        # NOT carry the marker -- matching the real client, whose receiving
        # process pops the marker before any local handler ever sees it
        # (client.py:351, before local dispatch). Carrying it into the local
        # twin would also break the per-topic-pair mirror guard's
        # payload+context fingerprint match (see
        # test_no_double_fire_dual_listener) and leak onto any descendant
        # frame a handler derives via forward()/reply().
        bus = FakeBus()
        got = []
        bus.on(LEGACY, lambda m: got.append(m))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(len(got), 1)
        self.assertNotIn(INTENT_COMPAT_TWIN_KEY, got[0].context)

    def test_no_double_fire_dual_listener(self):
        # a handler subscribed to BOTH the legacy and canonical topic must
        # not see the same logical dispatch twice -- matching the real
        # MessageBusClient, whose per-topic-pair mirror guard (shared by
        # every registration on either spelling) drops the twin as a
        # re-delivery of the same logical event. ovos-workshop 9.3.2a1+
        # binds the skill method to both spellings via a FRESH wrapper
        # closure per registration, so this must hold even though the two
        # ``bus.on()`` calls below pass the SAME underlying handler object.
        bus = FakeBus()
        calls = []
        handler = lambda m: calls.append(m.msg_type)
        bus.on(LEGACY, handler)
        bus.on(CANONICAL, handler)
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls, [CANONICAL])

    def test_independent_handlers_legacy_only_starves(self):
        # two INDEPENDENT handlers -- one on the canonical topic, one on the
        # legacy-only spelling -- share the per-topic-pair guard (it cannot
        # be scoped to a single handler, see FakeBus._mirror_guard_for), so
        # a canonical emit arms the guard and the legacy-only handler
        # starves. This matches real-bus behavior: a process holding both
        # handlers is unreachable from a single workshop version, so the
        # starvation is an accepted trade-off, not a defect.
        bus = FakeBus()
        canonical_calls = []
        legacy_calls = []
        bus.on(CANONICAL, lambda m: canonical_calls.append(m.msg_type))
        bus.on(LEGACY, lambda m: legacy_calls.append(m.msg_type))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(canonical_calls, [CANONICAL])
        self.assertEqual(legacy_calls, [])

    def test_twin_marker_does_not_leak_onto_unrelated_forward(self):
        # RULE 2 dedup marker regression: a handler on the LEGACY spelling
        # that forwards its received message's context onto an UNRELATED
        # suffixed topic must not brand that unrelated frame a twin. The
        # marker is popped BEFORE dispatch (mirrors
        # MessageBusClient.on_message's pop-before-dispatch ordering), so it
        # cannot survive onto a descendant frame created by
        # Message.forward(), which deep-copies context.
        bus = FakeBus()
        seen = []
        other_legacy = "other.skill:OtherIntent.intent"
        other_canonical = "other.skill:OtherIntent"

        def legacy_handler(m):
            bus.emit(m.forward(other_legacy, {}))

        bus.on(LEGACY, legacy_handler)
        bus.on(other_canonical, lambda m: seen.append("canonical-modernized"))
        bus.emit(Message(CANONICAL, {"utterance": "hi"}))
        self.assertEqual(seen, ["canonical-modernized"])

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
