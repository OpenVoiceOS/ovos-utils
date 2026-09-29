# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""OVOS-SESSION-2 §5.1 — a FakeBus never folds the default session on its
own observed traffic.

The §5.1 arrival merge is a once-per-utterance orchestrator-intake fold (see
core#915), not something every bus consumer repeats on every message it
sees. ``FakeBus`` models one bus connection for a test, so a test drives far
more default-session traffic through it than one fold per utterance --
``on_message`` must dispatch that traffic without folding it into the
``SessionManager`` singleton. A test that wants the orchestrator's own
intake semantics calls ``SessionManager.fold_inbound`` explicitly, exactly
as core's real intake does.
"""
import unittest

from ovos_utils.fakebus import FakeBus, FakeMessage

try:
    from ovos_bus_client.session import SessionManager
    HAS_BUS_CLIENT = True
except ImportError:
    HAS_BUS_CLIENT = False


@unittest.skipUnless(HAS_BUS_CLIENT, "ovos-bus-client not installed")
class TestFakeBusNeverFoldsObservedDefaultSession(unittest.TestCase):
    def setUp(self):
        SessionManager.reset_default_session()
        self.bus = FakeBus()

    def tearDown(self):
        SessionManager.reset_default_session()

    def _inbound(self, carrier):
        return FakeMessage("recognizer_loop:utterance",
                           {"utterances": ["hello"]},
                           {"session": carrier}).serialize()

    def test_observed_default_session_traffic_leaves_the_store_alone(self):
        stored = SessionManager.get_default_session()
        stored.lang = "pt-PT"
        stored.site_id = "kitchen"

        # a stale/minimal default carrier observed off the bus (e.g. an
        # ovos.utterance.handled ack from earlier in a pipeline) must not
        # wipe fields the live store has already moved past.
        self.bus.on_message(self._inbound({"session_id": "default"}))
        self.assertIs(SessionManager.get_default_session(), stored)
        self.assertEqual(stored.lang, "pt-PT")
        self.assertEqual(stored.site_id, "kitchen")

        # nor does a fully-populated observed carrier overwrite it -- that
        # fold belongs to the orchestrator's intake alone.
        self.bus.on_message(self._inbound({"session_id": "default",
                                           "site_id": "bedroom"}))
        self.assertEqual(stored.site_id, "kitchen")

    def test_emit_does_not_fold_the_default_session_either(self):
        # emit() runs on_message() internally before handlers -- confirm the
        # no-fold contract holds through the public emit() path too.
        stored = SessionManager.get_default_session()
        stored.site_id = "kitchen"
        from ovos_bus_client.message import Message
        self.bus.emit(Message("speak", {"utterance": "hi"},
                              {"session": {"session_id": "default",
                                          "site_id": "bedroom"}}))
        self.assertEqual(SessionManager.get_default_session().site_id,
                         "kitchen")


@unittest.skipUnless(HAS_BUS_CLIENT, "ovos-bus-client not installed")
class TestExplicitFoldInboundStillWorksAgainstAFakeBusMessage(unittest.TestCase):
    """The orchestrator's own explicit §5.1 fold is unaffected.

    A test simulating core's own intake still calls ``fold_inbound``
    explicitly -- this is that honest test shape, and it must still merge
    field-by-field the way §5.1 describes.
    """

    def setUp(self):
        SessionManager.reset_default_session()

    def tearDown(self):
        SessionManager.reset_default_session()

    def test_explicit_fold_inbound_merges_field_by_field(self):
        from ovos_bus_client.message import Message
        first = Message.deserialize(
            FakeMessage("recognizer_loop:utterance", {"utterances": ["hi"]},
                       {"session": {"session_id": "default",
                                    "lang": "pt-pt",
                                    "site_id": "kitchen"}}).serialize())
        SessionManager.fold_inbound(first)
        stored = SessionManager.get_default_session()
        self.assertEqual(stored.lang, "pt-PT")
        self.assertEqual(stored.site_id, "kitchen")

        second = Message.deserialize(
            FakeMessage("recognizer_loop:utterance", {"utterances": ["hi"]},
                       {"session": {"session_id": "default"}}).serialize())
        SessionManager.fold_inbound(second)
        self.assertIs(SessionManager.get_default_session(), stored)
        self.assertEqual(stored.lang, "pt-PT")
        self.assertEqual(stored.site_id, "kitchen")


if __name__ == "__main__":
    unittest.main()
