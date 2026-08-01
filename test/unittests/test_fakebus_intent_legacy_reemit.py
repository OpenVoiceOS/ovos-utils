"""FakeBus mirrors MessageBusClient's legacy intent-topic bridge.

Old ovos-workshop built the per-intent dispatch topic from the resource
filename, so ``<skill_id>:food.order.intent`` reached the wire. Current
workshop registers the canonical ``<skill_id>:food.order``. When emit_legacy
is on, a bus that has a handler bound to the suffixed spelling also gets the
dispatch mirrored onto that spelling.

Both fake buses must behave like the real client, otherwise every harness
built on them hides the compat path.
"""
import asyncio
import unittest

from ovos_spec_tools import Message

from ovos_utils.fakebus import (INTENT_REEMIT_CONTEXT_KEY, AsyncFakeBus,
                                FakeBus)

CANONICAL = "skill-food.jarbas:food.order"
LEGACY = "skill-food.jarbas:food.order.intent"


def _run(coro):
    return asyncio.run(coro)


class TestAliasDrivenReemit(unittest.TestCase):
    def test_suffixed_subscription_receives_canonical_dispatch(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {"utterance": "one pizza"}))
        self.assertEqual([m.msg_type for m in got], [LEGACY])
        self.assertEqual(got[0].data, {"utterance": "one pizza"})

    def test_mirror_keeps_data_and_context(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {"a": 1}, {"source": ["me"]}))
        self.assertEqual(got[0].data, {"a": 1})
        self.assertEqual(got[0].context["source"], ["me"])

    def test_mirror_is_marked_in_context(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertTrue(got[0].context[INTENT_REEMIT_CONTEXT_KEY])

    def test_no_mirror_without_a_suffixed_subscription(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual([m.msg_type for m in got], [CANONICAL])

    def test_once_subscription_also_registers_the_alias(self):
        bus = FakeBus()
        got = []
        bus.once(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual([m.msg_type for m in got], [LEGACY])

    def test_non_intent_topics_are_never_mirrored(self):
        bus = FakeBus()
        got = []
        bus.on("ovos.utterance.handled.intent", got.append)
        bus.emit(Message("ovos.utterance.handled"))
        self.assertEqual(got, [])


class TestExactlyOnce(unittest.TestCase):
    def test_one_dispatch_yields_one_mirror(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(len(got), 1)

    def test_two_suffixed_handlers_each_run_once(self):
        bus = FakeBus()
        a, b = [], []
        bus.on(LEGACY, a.append)
        bus.on(LEGACY, b.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual((len(a), len(b)), (1, 1))

    def test_handler_on_both_spellings_gets_both_topics_once_each(self):
        # the intent bridge does not dedupe across spellings - a handler bound
        # to both asked for both. Workshop collapses aliases at registration.
        bus = FakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual([m.msg_type for m in got], [CANONICAL, LEGACY])


class TestLoopPrevention(unittest.TestCase):
    def test_a_legacy_dispatch_is_not_mirrored_again(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.on(CANONICAL, got.append)
        bus.emit(Message(LEGACY))
        self.assertEqual([m.msg_type for m in got], [LEGACY])

    def test_a_marked_message_is_not_mirrored(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL, {}, {INTENT_REEMIT_CONTEXT_KEY: True}))
        self.assertEqual(got, [])

    def test_reemitting_a_mirror_terminates(self):
        bus = FakeBus(intent_reemit_blanket=True)
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        bus.emit(got[0])  # feed the twin back in
        self.assertEqual(len(got), 2)


class TestBlanketMode(unittest.TestCase):
    def test_blanket_mirrors_without_any_registration(self):
        bus = FakeBus(intent_reemit_blanket=True)
        got = []
        bus.ee.on(LEGACY, got.append)  # subscribe behind the bus's back
        bus.emit(Message(CANONICAL))
        self.assertEqual([m.msg_type for m in got], [LEGACY])

    def test_blanket_off_by_default(self):
        bus = FakeBus()
        got = []
        bus.ee.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])

    def test_blanket_still_skips_non_intent_topics(self):
        bus = FakeBus(intent_reemit_blanket=True)
        got = []
        bus.ee.on("ovos.utterance.handled.intent", got.append)
        bus.emit(Message("ovos.utterance.handled"))
        self.assertEqual(got, [])


class TestDisabled(unittest.TestCase):
    def test_no_mirror_when_emit_legacy_is_off(self):
        bus = FakeBus(emit_legacy=False)
        got = []
        bus.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])

    def test_no_mirror_when_emit_legacy_is_off_even_in_blanket(self):
        bus = FakeBus(emit_legacy=False, intent_reemit_blanket=True)
        got = []
        bus.ee.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])

    def test_no_mirror_without_spec_tools_intent_support(self):
        bus = FakeBus()
        bus._intent_aliases = None  # older spec-tools: helpers not importable
        got = []
        bus.ee.on(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])


class TestAliasLifecycle(unittest.TestCase):
    def test_removing_the_last_suffixed_handler_stops_the_mirror(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.remove(LEGACY, got.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])

    def test_remove_all_listeners_stops_the_mirror(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY, got.append)
        bus.remove_all_listeners(LEGACY)
        bus.emit(Message(CANONICAL))
        self.assertEqual(got, [])

    def test_one_removal_of_two_handlers_keeps_the_mirror(self):
        bus = FakeBus()
        a, b = [], []
        bus.on(LEGACY, a.append)
        bus.on(LEGACY, b.append)
        bus.remove(LEGACY, a.append)
        bus.emit(Message(CANONICAL))
        self.assertEqual(len(b), 1)


class TestAsyncFakeBusParity(unittest.TestCase):
    def test_suffixed_subscription_receives_canonical_dispatch(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(LEGACY, got.append)
        _run(bus.emit(Message(CANONICAL, {"utterance": "one pizza"})))
        self.assertEqual([m.msg_type for m in got], [LEGACY])
        self.assertEqual(got[0].data, {"utterance": "one pizza"})

    def test_no_mirror_without_a_suffixed_subscription(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(CANONICAL, got.append)
        _run(bus.emit(Message(CANONICAL)))
        self.assertEqual([m.msg_type for m in got], [CANONICAL])

    def test_legacy_dispatch_is_not_mirrored_again(self):
        bus = AsyncFakeBus()
        got = []
        bus.on(LEGACY, got.append)
        _run(bus.emit(Message(LEGACY)))
        self.assertEqual(len(got), 1)

    def test_blanket_mode(self):
        bus = AsyncFakeBus(intent_reemit_blanket=True)
        got = []
        bus.ee.on(LEGACY, got.append)
        _run(bus.emit(Message(CANONICAL)))
        self.assertEqual([m.msg_type for m in got], [LEGACY])

    def test_no_mirror_when_emit_legacy_is_off(self):
        bus = AsyncFakeBus(emit_legacy=False)
        got = []
        bus.on(LEGACY, got.append)
        _run(bus.emit(Message(CANONICAL)))
        self.assertEqual(got, [])


if __name__ == "__main__":
    unittest.main()
