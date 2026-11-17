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
"""OVOS-SESSION-1 §2.5 (architecture dev 198a3c9) -- a malformed session
carrier drops the whole message rather than crashing the consumer or its
transport, and the drop is observable: the bus emits
``ovos.session.rejected`` naming the dropped message's type and reason.

``ovos_bus_client.client.client.MessageBusClient.on_message`` wraps its
session intake in ``try/except MalformedSession`` for exactly this reason
(see ``client.py`` around ``_take_inbound_session``): a non-object
``context.session`` is a per-message producer fault, not a transport fault.
``FakeBus``/``AsyncFakeBus`` must mirror that: drop the malformed message
without delivering it to listeners, and emit the rejection notice, which
itself carries no session and is delivered normally.
"""
import asyncio
import unittest

from ovos_spec_tools.messages import SpecMessage

from ovos_utils.fakebus import AsyncFakeBus, FakeBus, FakeMessage

try:
    from ovos_bus_client.session import SessionManager
    HAS_BUS_CLIENT = True
except ImportError:
    HAS_BUS_CLIENT = False


@unittest.skipUnless(HAS_BUS_CLIENT, "ovos-bus-client not installed")
class TestFakeBusMalformedSessionIsRejected(unittest.TestCase):
    def setUp(self):
        SessionManager.reset_default_session()
        self.bus = FakeBus()

    def tearDown(self):
        SessionManager.reset_default_session()

    def test_malformed_carrier_is_dropped_and_rejected(self):
        dropped = []
        rejected = []
        self.bus.on("x", dropped.append)
        self.bus.on(SpecMessage.SESSION_REJECTED, rejected.append)

        # context.session is a string, not an object -- malformed per §2.5.
        message = FakeMessage("x", {}, {"session": "notanobject"})
        self.bus.emit(message)  # must not raise

        self.assertEqual(dropped, [])
        self.assertEqual(len(rejected), 1)
        notice = rejected[0]
        self.assertEqual(notice.msg_type, SpecMessage.SESSION_REJECTED)
        self.assertEqual(notice.data, {"msg_type": "x",
                                       "reason": "malformed_carrier"})
        self.assertNotIn("session", notice.context)

    def test_utterance_id_carried_onto_the_rejection_when_present(self):
        rejected = []
        self.bus.on(SpecMessage.SESSION_REJECTED, rejected.append)

        message = FakeMessage("x", {}, {"session": "notanobject",
                                        "utterance_id": "abc-123"})
        self.bus.emit(message)

        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].context.get("utterance_id"), "abc-123")
        self.assertNotIn("session", rejected[0].context)

    def test_well_formed_message_is_still_delivered_normally(self):
        received = []
        self.bus.on("x", received.append)

        message = FakeMessage("x", {}, {})
        self.bus.emit(message)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].msg_type, "x")


@unittest.skipUnless(HAS_BUS_CLIENT, "ovos-bus-client not installed")
class TestAsyncFakeBusMalformedSessionIsRejected(unittest.TestCase):
    def setUp(self):
        SessionManager.reset_default_session()
        self.bus = AsyncFakeBus()

    def tearDown(self):
        SessionManager.reset_default_session()

    def test_malformed_carrier_is_dropped_and_rejected(self):
        dropped = []
        rejected = []
        self.bus.on("x", dropped.append)
        self.bus.on(SpecMessage.SESSION_REJECTED, rejected.append)

        message = FakeMessage("x", {}, {"session": "notanobject"})
        asyncio.run(self.bus.emit(message))  # must not raise

        self.assertEqual(dropped, [])
        self.assertEqual(len(rejected), 1)
        notice = rejected[0]
        self.assertEqual(notice.msg_type, SpecMessage.SESSION_REJECTED)
        self.assertEqual(notice.data, {"msg_type": "x",
                                       "reason": "malformed_carrier"})
        self.assertNotIn("session", notice.context)

    def test_well_formed_message_is_still_delivered_normally(self):
        received = []
        self.bus.on("x", received.append)

        message = FakeMessage("x", {}, {})
        asyncio.run(self.bus.emit(message))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].msg_type, "x")
