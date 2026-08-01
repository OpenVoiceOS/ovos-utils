"""Guards for the post-compat world: FakeBus carries no legacy wire bridge.

These are the inverted twins of the old
``test_fakebus_namespace_migration.py`` and
``test_fakebus_intent_legacy_reemit.py``. Those files proved the bridge
worked; this one proves it is absent.

A test double that kept the bridge would be worse than useless — every
harness built on it would pass against behaviour the real
``MessageBusClient`` no longer has.
"""
import unittest
from unittest.mock import patch

from ovos_utils import fakebus as fakebus_mod
from ovos_utils.fakebus import FakeBus, FakeMessage
from ovos_spec_tools import MIGRATION_MAP

LEGACY_SPEAK = "speak"
SPEC_SPEAK = MIGRATION_MAP[LEGACY_SPEAK].value
SKILL_ID = "ovos-skill-fake.openvoiceos"
CANONICAL_INTENT = f"{SKILL_ID}:food.order"
LEGACY_INTENT = f"{CANONICAL_INTENT}.intent"


class TestNoNamespaceBridge(unittest.TestCase):
    def test_spec_emit_does_not_reach_legacy_listeners(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY_SPEAK, lambda m: got.append(m.msg_type))
        bus.emit(FakeMessage(SPEC_SPEAK, {"utterance": "hi"}))
        self.assertEqual(got, [])

    def test_legacy_emit_does_not_reach_spec_listeners(self):
        bus = FakeBus()
        got = []
        bus.on(SPEC_SPEAK, lambda m: got.append(m.msg_type))
        bus.emit(FakeMessage(LEGACY_SPEAK, {"utterance": "hi"}))
        self.assertEqual(got, [])

    def test_no_migrated_topic_is_bridged_in_either_direction(self):
        """Sweep the whole map rather than trusting one sample pair."""
        for legacy, spec in MIGRATION_MAP.items():
            with self.subTest(topic=legacy):
                bus = FakeBus()
                seen = []
                bus.on(legacy, lambda m: seen.append("legacy"))
                bus.on(spec.value, lambda m: seen.append("spec"))
                bus.emit(FakeMessage(spec.value))
                self.assertEqual(seen, ["spec"])
                seen.clear()
                bus.emit(FakeMessage(legacy))
                self.assertEqual(seen, ["legacy"])

    def test_handler_on_both_namespaces_is_no_longer_deduped(self):
        bus = FakeBus()
        calls = []

        def handler(message):
            calls.append(message.msg_type)

        bus.on(LEGACY_SPEAK, handler)
        bus.on(SPEC_SPEAK, handler)
        bus.emit(FakeMessage(SPEC_SPEAK))
        bus.emit(FakeMessage(LEGACY_SPEAK))
        self.assertEqual(calls, [SPEC_SPEAK, LEGACY_SPEAK])

    def test_on_registers_the_handler_itself_not_a_wrapper(self):
        bus = FakeBus()

        def handler(message):
            pass

        bus.on(SPEC_SPEAK, handler)
        self.assertEqual(bus.ee.listeners(SPEC_SPEAK), [handler])
        bus.remove(SPEC_SPEAK, handler)
        self.assertEqual(bus.ee.listeners(SPEC_SPEAK), [])


class TestNoIntentTopicTwin(unittest.TestCase):
    def test_canonical_dispatch_does_not_reach_the_suffixed_twin(self):
        bus = FakeBus()
        got = []
        bus.on(LEGACY_INTENT, lambda m: got.append(m.msg_type))
        bus.emit(FakeMessage(CANONICAL_INTENT, {"utterance": "order food"}))
        self.assertEqual(got, [])

    def test_canonical_listener_still_receives_the_canonical_dispatch(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL_INTENT, lambda m: got.append(m.msg_type))
        bus.emit(FakeMessage(CANONICAL_INTENT, {"utterance": "order food"}))
        self.assertEqual(got, [CANONICAL_INTENT])

    def test_no_reemit_marker_is_stamped_on_the_dispatch(self):
        bus = FakeBus()
        got = []
        bus.on(CANONICAL_INTENT, lambda m: got.append(m))
        bus.emit(FakeMessage(CANONICAL_INTENT))
        self.assertNotIn("__legacy_intent_reemit__", got[0].context)


class TestBridgeSurfaceIsGone(unittest.TestCase):
    def test_module_exports_no_bridge_symbols(self):
        for name in ("INTENT_REEMIT_CONTEXT_KEY", "IntentAliasRegistry",
                     "legacy_reemit_targets", "NamespaceTranslator",
                     "_LegacyIntentBridge", "_resolve_bus_flags"):
            self.assertFalse(hasattr(fakebus_mod, name), name)

    def test_instances_carry_no_bridge_state(self):
        bus = FakeBus()
        for name in ("_translator", "_handler_guards", "_dedup_registrations",
                     "_intent_aliases", "_intent_reemit_blanket"):
            self.assertFalse(hasattr(bus, name), name)


class TestRemovedFlagsAreLoud(unittest.TestCase):
    def test_kwarg_is_accepted_and_ignored(self):
        """A harness kwarg is not an operator decision — it warns, not raises,
        so every ecosystem harness that still passes it keeps booting."""
        for key in ("emit_legacy", "modernize", "intent_reemit_blanket"):
            with self.subTest(key=key):
                bus = FakeBus(**{key: True})
                got = []
                bus.on(LEGACY_SPEAK, lambda m: got.append(m.msg_type))
                bus.emit(FakeMessage(SPEC_SPEAK))
                self.assertEqual(got, [])

    def test_env_flag_raises(self):
        for env_var in ("OVOS_BUS_EMIT_LEGACY", "OVOS_BUS_MODERNIZE",
                        "OVOS_BUS_INTENT_REEMIT_BLANKET"):
            with self.subTest(env_var=env_var):
                with patch.dict(fakebus_mod.environ, {env_var: "true"}):
                    with self.assertRaises(RuntimeError):
                        FakeBus()

    def test_explicitly_disabled_flags_are_accepted(self):
        FakeBus(emit_legacy=False, modernize=False,
                intent_reemit_blanket=False)


if __name__ == "__main__":
    unittest.main()
