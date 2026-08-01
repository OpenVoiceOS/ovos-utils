"""FakeBus mirrors MessageBusClient's legacy intent-topic bridge.

Old ovos-workshop built the per-intent dispatch topic from the resource
filename, so ``<skill_id>:food.order.intent`` reached the wire. Current
workshop registers the canonical ``<skill_id>:food.order``. The bridge is two
stateless rules. The real client splits them over a wire send and a wire
receive; a fake bus is one process, so both land in ``emit``:

* a CANONICAL dispatch also fires its suffixed twin, marked as a twin;
* a SUFFIXED dispatch that is not already such a twin also fires its canonical
  spelling.

Both fake buses must behave like the real client, otherwise every harness
built on them hides the compat path.
"""
import asyncio
import unittest

from ovos_spec_tools import Message

from ovos_utils.fakebus import (INTENT_COMPAT_TWIN_KEY, AsyncFakeBus, FakeBus)

CANONICAL = "skill-food.jarbas:food.order"
LEGACY = "skill-food.jarbas:food.order.intent"


def _run(coro):
    return asyncio.run(coro)


class TestCanonicalDispatch(unittest.TestCase):
    """Rule 1: a canonical dispatch also fires the marked suffixed twin."""

    def test_suffixed_handler_receives_the_twin(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {"utterance": "one pizza"}))
        self.assertEqual([m.msg_type for m in got], [LEGACY])
        self.assertEqual(got[0].data, {"utterance": "one pizza"})

    def test_twin_keeps_context_but_is_delivered_unmarked(self):
        # the twin keeps the ordinary context it forwards, but the dedup marker
        # must NOT reach local handlers: it would ride forward()/reply() onto
        # any follow-up message a handler emits and suppress its modernization.
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {"a": 1}, {"source": ["me"]}))
        self.assertEqual(got[0].context["source"], ["me"])
        self.assertNotIn(INTENT_COMPAT_TWIN_KEY, got[0].context)

    def test_twin_carries_the_marker_on_the_wire(self):
        # wire survival: the serialized twin on the "message" firehose keeps the
        # marker, so a receiver in another process still skips re-modernizing it.
        import json
        bus = FakeBus()
        wire = []
        bus.on("message", lambda m: wire.append(json.loads(m)))
        bus.emit(Message(CANONICAL))
        twins = [f for f in wire if f["type"] == LEGACY]
        self.assertEqual(len(twins), 1)
        self.assertTrue(twins[0]["context"][INTENT_COMPAT_TWIN_KEY])

    def test_canonical_handler_fires_exactly_once(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.on(LEGACY, lambda m: None)
        bus.emit(Message(CANONICAL))
        self.assertEqual(len(got), 1)

    def test_a_handler_on_both_spellings_hears_both_frames_once_each(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual([m.msg_type for m in got], [CANONICAL, LEGACY])

    def test_no_twin_when_compat_is_disabled(self):
        bus = FakeBus(emit_legacy=False)
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])


class TestSuffixedDispatch(unittest.TestCase):
    """Rule 2: an unmarked suffixed dispatch also fires the canonical form."""

    def test_canonical_handler_hears_an_old_style_dispatch(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.emit(Message(LEGACY, {"utterance": "one pizza"}))
        self.assertEqual([m.msg_type for m in got], [CANONICAL])
        self.assertEqual(got[0].data, {"utterance": "one pizza"})

    def test_suffixed_handler_still_gets_the_original(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(LEGACY))
        self.assertEqual(len(got), 1)

    def test_a_marked_twin_is_not_modernized_again(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.emit(Message(LEGACY, {}, {INTENT_COMPAT_TWIN_KEY: True}))
        self.assertEqual(got, [])

    def test_the_bridge_does_not_cascade(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(LEGACY))
        self.assertEqual(len(got), 1)  # not re-twinned off its own canonical

    def test_no_modernization_when_compat_is_disabled(self):
        bus = FakeBus(emit_legacy=False)
        got = []
        bus.on(CANONICAL, got.append)
        bus.emit(Message(LEGACY))
        self.assertEqual(got, [])


class TestMarkerDoesNotLeakToDescendants(unittest.TestCase):
    """The twin marker must not ride forward()/reply() onto later messages.

    Message.forward()/reply() deep-copy the whole context. If a delivered twin
    kept the marker, a handler that forwards that context to emit an UNRELATED
    suffixed intent would brand the follow-up a twin, and the bridge would
    silently drop its canonical spelling.
    """

    UNRELATED_LEGACY = "other-skill.jarbas:unrelated.intent"
    UNRELATED_CANON = "other-skill.jarbas:unrelated"

    def test_forward_off_a_twin_does_not_suppress_an_unrelated_intent(self):
        bus = FakeBus()
        seen_twin = []
        bus.on(LEGACY, seen_twin.append)
        bus.emit(Message(CANONICAL, {"utterance": "one pizza"}))
        twin_msg = seen_twin[0]
        self.assertNotIn(INTENT_COMPAT_TWIN_KEY, twin_msg.context)
        # a handler forwards this frame's context to emit an unrelated intent.
        got_canon = []
        bus.on(self.UNRELATED_CANON, got_canon.append)
        followup = twin_msg.forward(self.UNRELATED_LEGACY, {})
        self.assertNotIn(INTENT_COMPAT_TWIN_KEY, followup.context)
        bus.emit(followup)
        # the unrelated canonical topic IS modernized: the marker did not leak.
        self.assertEqual([m.msg_type for m in got_canon], [self.UNRELATED_CANON])

    def test_reply_off_a_twin_does_not_suppress_an_unrelated_intent(self):
        bus = FakeBus()
        seen_twin = []
        bus.on(LEGACY, seen_twin.append)
        bus.emit(Message(CANONICAL))
        got_canon = []
        bus.on(self.UNRELATED_CANON, got_canon.append)
        bus.emit(seen_twin[0].reply(self.UNRELATED_LEGACY, {}))
        self.assertEqual([m.msg_type for m in got_canon], [self.UNRELATED_CANON])

    def test_marker_survives_on_the_wire_for_a_second_receiver(self):
        # a marked frame emitted (as if arriving from the wire) is delivered to
        # its legacy listener but NOT re-modernized: wire survival intact.
        bus = FakeBus()
        got_legacy = []
        got_canon = []
        bus.on(LEGACY, got_legacy.append)
        bus.on(CANONICAL, got_canon.append)
        bus.emit(Message(LEGACY, {}, {INTENT_COMPAT_TWIN_KEY: True}))
        self.assertEqual(len(got_legacy), 1)
        self.assertEqual(len(got_canon), 0)


class TestNonIntentTopics(unittest.TestCase):
    def test_dotted_topics_are_untouched(self):
        bus = FakeBus()
        got = []
        bus.on("ovos.utterance.handled", got.append)
        bus.emit(Message("ovos.utterance.handled"))
        self.assertEqual(len(got), 1)

    def test_nothing_extra_is_dispatched(self):
        bus = FakeBus()
        got = []
        bus.on("message", got.append)
        bus.emit(Message("ovos.utterance.handled"))
        self.assertEqual(len(got), 1)


class TestAsyncFakeBus(unittest.TestCase):
    """The async double runs the same two rules."""

    def test_canonical_dispatch_fires_the_twin(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(LEGACY, got.append)
        _run(bus.emit(Message(CANONICAL)))
        self.assertEqual([m.msg_type for m in got], [LEGACY])
        # delivered unmarked (no leak onto descendants); marker rides the wire
        self.assertNotIn(INTENT_COMPAT_TWIN_KEY, got[0].context)

    def test_suffixed_dispatch_fires_the_canonical_form(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        _run(bus.emit(Message(LEGACY)))
        self.assertEqual([m.msg_type for m in got], [CANONICAL])

    def test_no_bridge_when_compat_is_disabled(self):
        bus = AsyncFakeBus(emit_legacy=False)
        got = []
        bus.on(LEGACY, got.append)
        _run(bus.emit(Message(CANONICAL)))
        self.assertEqual(got, [])


if __name__ == "__main__":
    unittest.main()
