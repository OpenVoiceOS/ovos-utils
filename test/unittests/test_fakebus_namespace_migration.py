"""FakeBus mirrors MessageBusClient's legacy<->ovos.* namespace migration, so
e2e/satellite tests exercise the real cross-namespace behaviour."""
import asyncio
import unittest
from unittest.mock import patch

from ovos_utils.fakebus import AsyncFakeBus, FakeBus, Message


def _run(coro):
    return asyncio.run(coro)


class TestFakeBusNamespaceMigration(unittest.TestCase):
    def test_legacy_emit_reaches_spec_listener(self):
        bus = FakeBus()  # both flags default on
        got = []
        bus.on("ovos.utterance.speak", lambda m: got.append(m.msg_type))
        bus.emit(Message("speak", {"utterance": "hi"}))
        self.assertEqual(got, ["ovos.utterance.speak"])  # modernize bridged it

    def test_spec_emit_reaches_legacy_listener(self):
        bus = FakeBus()
        got = []
        bus.on("speak", lambda m: got.append(m.msg_type))
        bus.emit(Message("ovos.utterance.speak", {"utterance": "hi"}))
        self.assertEqual(got, ["speak"])  # emit_legacy bridged it

    def test_dual_listener_fires_once(self):
        bus = FakeBus()
        calls = []
        handler = lambda m: calls.append(m.msg_type)
        bus.on("speak", handler)
        bus.on("ovos.utterance.speak", handler)
        bus.emit(Message("speak", {"utterance": "hi"}))
        self.assertEqual(len(calls), 1)  # mirror deduped

    def test_distinct_listeners_each_fire_once(self):
        bus = FakeBus()
        legacy, spec = [], []
        bus.on("speak", lambda m: legacy.append(1))
        bus.on("ovos.utterance.speak", lambda m: spec.append(1))
        bus.emit(Message("speak", {"utterance": "hi"}))
        self.assertEqual((len(legacy), len(spec)), (1, 1))

    def test_flags_off_no_bridging(self):
        bus = FakeBus(modernize=False, emit_legacy=False)
        got = []
        bus.on("ovos.utterance.speak", lambda m: got.append(m.msg_type))
        bus.emit(Message("speak", {"utterance": "hi"}))
        self.assertEqual(got, [])  # no translation -> spec listener not reached

    def test_unmapped_topic_untouched(self):
        bus = FakeBus()
        got = []
        bus.on("my.custom.topic", lambda m: got.append(m.msg_type))
        bus.emit(Message("my.custom.topic", {"x": 1}))
        self.assertEqual(got, ["my.custom.topic"])

    def test_shape_changing_payload_reshaped_for_spec_listener(self):
        # a spec listener on the counterpart of a SHAPE-CHANGING legacy topic
        # receives the payload in ITS shape, not a verbatim legacy copy.
        bus = FakeBus()
        got = []
        bus.on("ovos.intent.handler.start", lambda m: got.append(dict(m.data)))
        bus.emit(Message("mycroft.skill.handler.start", {"handler": "HelloIntent"}))
        self.assertEqual(len(got), 1)
        # reshaped to the spec shape ({"intent_name": ...}), NOT {"handler": ...}
        self.assertEqual(got[0], {"intent_name": "HelloIntent"})
        self.assertNotIn("handler", got[0])

    def test_shape_changing_payload_reshaped_for_legacy_listener(self):
        bus = FakeBus()
        got = []
        bus.on("mycroft.skill.handler.start", lambda m: got.append(dict(m.data)))
        bus.emit(Message("ovos.intent.handler.start",
                         {"skill_id": "skill.foo", "intent_name": "HelloIntent"}))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].get("handler"), "HelloIntent")  # legacy shape

    def test_payload_compatible_rename_delivered_equivalent(self):
        bus = FakeBus()
        got = []
        bus.on("ovos.utterance.speak", lambda m: got.append(dict(m.data)))
        bus.emit(Message("speak", {"utterance": "hi", "lang": "en-us"}))
        self.assertEqual(got, [{"utterance": "hi", "lang": "en-us"}])  # identity

    def test_remove_cleans_up(self):
        bus = FakeBus()
        calls = []
        handler = lambda m: calls.append(1)
        bus.on("speak", handler)
        bus.on("ovos.utterance.speak", handler)
        bus.remove("speak", handler)
        bus.remove("ovos.utterance.speak", handler)
        self.assertNotIn(handler, bus._handler_guards)
        bus.emit(Message("speak", {"utterance": "hi"}))
        self.assertEqual(calls, [])


class TestFakeBusFlagResolution(unittest.TestCase):
    """When the kwarg is omitted, flags resolve via env -> websocket.* config ->
    default True, matching MessageBusClient._bus_flag. An explicit kwarg wins."""

    def _legacy_mirrored(self, bus):
        # emit a legacy topic; if emit_legacy bridging is on a spec listener fires
        got = []
        bus.on("ovos.utterance.speak", lambda m: got.append(m.msg_type))
        if isinstance(bus, AsyncFakeBus):
            _run(bus.emit(Message("speak", {"utterance": "hi"})))
        else:
            bus.emit(Message("speak", {"utterance": "hi"}))
        return got == ["ovos.utterance.speak"]

    def test_default_true_no_env_mirrors(self):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("OVOS_BUS_MODERNIZE", None)
            os.environ.pop("OVOS_BUS_EMIT_LEGACY", None)
            self.assertTrue(self._legacy_mirrored(FakeBus()))
            self.assertTrue(self._legacy_mirrored(AsyncFakeBus()))

    def test_env_false_disables_mirror(self):
        with patch.dict("os.environ",
                        {"OVOS_BUS_MODERNIZE": "false",
                         "OVOS_BUS_EMIT_LEGACY": "false"}):
            self.assertFalse(self._legacy_mirrored(FakeBus()))
            self.assertFalse(self._legacy_mirrored(AsyncFakeBus()))

    def test_explicit_kwarg_beats_env(self):
        # env says off, but an explicit modernize=True kwarg still mirrors
        with patch.dict("os.environ",
                        {"OVOS_BUS_MODERNIZE": "false",
                         "OVOS_BUS_EMIT_LEGACY": "false"}):
            self.assertTrue(self._legacy_mirrored(FakeBus(modernize=True)))
            self.assertTrue(self._legacy_mirrored(AsyncFakeBus(modernize=True)))

    def test_explicit_false_kwarg_beats_unset_env(self):
        import os
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("OVOS_BUS_MODERNIZE", None)
            os.environ.pop("OVOS_BUS_EMIT_LEGACY", None)
            # default would mirror; explicit modernize=False suppresses it
            self.assertFalse(self._legacy_mirrored(FakeBus(modernize=False)))
            self.assertFalse(self._legacy_mirrored(AsyncFakeBus(modernize=False)))


if __name__ == "__main__":
    unittest.main()
