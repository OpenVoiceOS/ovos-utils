"""A handler bound to both spellings of a migrated topic runs once per emit,
whatever session the message carries.

PIPELINE-1 appendix divergences: "A transitional deployment MAY subscribe to
both names during migration." FakeBus delivers a listener on either namespace
the event; the per-handler mirror guard collapses the twin.
"""
import unittest

from ovos_spec_tools import Message

from ovos_utils.fakebus import FakeBus

SPEC = "ovos.utterance.handle"
LEGACY = "recognizer_loop:utterance"
SESSIONS = {
    "absent": None,
    "default": {"session_id": "default"},
    "named": {"session_id": "kitchen"},
    "nat_default": {"session_id": "nsA:default"},
}


def _message(topic, session):
    context = {} if session is None else {"session": dict(session)}
    return Message(topic, {"utterances": ["hello"], "lang": "en-US"}, context)


class TestCounterpartDedup(unittest.TestCase):
    def test_dual_subscribed_handler_runs_once_per_emit(self):
        for emit_legacy in (True, False):
            for topic in (SPEC, LEGACY):
                for name, session in SESSIONS.items():
                    with self.subTest(emit_legacy=emit_legacy, topic=topic,
                                      session=name):
                        bus = FakeBus(emit_legacy=emit_legacy)
                        calls = []
                        def handler(m, calls=calls):
                            calls.append(m.msg_type)
                        bus.on(SPEC, handler)
                        bus.on(LEGACY, handler)
                        bus.emit(_message(topic, session))
                        self.assertEqual(calls, [topic])

    def test_counterpart_keeps_the_original_context(self):
        for name, session in SESSIONS.items():
            with self.subTest(session=name):
                bus = FakeBus()
                seen = {}
                bus.on(SPEC, lambda m: seen.setdefault("spec", m))
                bus.on(LEGACY, lambda m: seen.setdefault("legacy", m))
                bus.emit(_message(LEGACY, session))
                self.assertEqual(seen["spec"].msg_type, SPEC)
                self.assertEqual(seen["spec"].context, seen["legacy"].context)
                self.assertEqual(seen["spec"].data, seen["legacy"].data)

    def test_single_topic_listener_receives_the_counterpart(self):
        for name, session in SESSIONS.items():
            with self.subTest(session=name):
                bus = FakeBus()
                got = []
                bus.on(SPEC, lambda m: got.append((m.msg_type, m.data)))
                bus.emit(_message(LEGACY, session))
                self.assertEqual(
                    got, [(SPEC, {"utterances": ["hello"], "lang": "en-US"})])
