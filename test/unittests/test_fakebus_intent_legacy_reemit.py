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

    def test_twin_is_marked_and_keeps_context(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {"a": 1}, {"source": ["me"]}))
        self.assertEqual(got[0].context["source"], ["me"])
        self.assertTrue(got[0].context[INTENT_COMPAT_TWIN_KEY])

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
        self.assertTrue(got[0].context[INTENT_COMPAT_TWIN_KEY])

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
