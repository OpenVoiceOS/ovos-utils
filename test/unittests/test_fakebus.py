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
#
import unittest
import warnings

from ovos_utils.fakebus import FakeBus, FakeMessage


class TestFakeMessage(unittest.TestCase):
    def _make_message(self, msg_type: str, data: dict = None,
                      context: dict = None) -> FakeMessage:
        # FakeMessage may return a real Message object if ovos_bus_client is installed
        return FakeMessage(msg_type, data, context)

    def test_basic_construction(self) -> None:
        msg = self._make_message("test.type", {"key": "value"}, {"ctx": 1})
        self.assertEqual(msg.msg_type, "test.type")
        self.assertEqual(msg.data["key"], "value")
        self.assertEqual(msg.context["ctx"], 1)

    def test_defaults(self) -> None:
        msg = self._make_message("test.type")
        self.assertEqual(msg.data, {})
        self.assertEqual(msg.context, {})

    def test_serialize_deserialize(self) -> None:
        msg = self._make_message("test.roundtrip", {"x": 42})
        serialized = msg.serialize()
        restored = FakeMessage.deserialize(serialized)
        self.assertEqual(restored.msg_type, "test.roundtrip")
        self.assertEqual(restored.data["x"], 42)

    def test_forward(self) -> None:
        msg = self._make_message("original.type", {}, {"source": "skill"})
        fwd = msg.forward("forwarded.type", {"new": "data"})
        self.assertEqual(fwd.msg_type, "forwarded.type")
        self.assertEqual(fwd.context["source"], "skill")

    def test_reply(self) -> None:
        msg = self._make_message("request.type", {}, {"source": "a", "destination": "b"})
        reply = msg.reply("reply.type", {"answer": 1})
        self.assertEqual(reply.msg_type, "reply.type")

    def test_response(self) -> None:
        msg = self._make_message("my.request")
        resp = msg.response({"result": "ok"})
        self.assertEqual(resp.msg_type, "my.request.response")
        self.assertEqual(resp.data["result"], "ok")

    def test_equality(self) -> None:
        m1 = self._make_message("same.type", {"a": 1}, {})
        m2 = self._make_message("same.type", {"a": 1}, {})
        self.assertEqual(m1, m2)

    def test_inequality(self) -> None:
        m1 = self._make_message("type.a", {"x": 1})
        m2 = self._make_message("type.b", {"x": 1})
        self.assertNotEqual(m1, m2)

    def test_deserialize_empty_type(self) -> None:
        import json
        raw = json.dumps({"type": "", "data": {}, "context": {}})
        msg = FakeMessage.deserialize(raw)
        self.assertEqual(msg.msg_type, "")


class TestFakeBus(unittest.TestCase):
    def test_construction(self) -> None:
        bus = FakeBus()
        self.assertIsNotNone(bus)
        self.assertEqual(bus.session_id, "default")

    def test_run_forever(self) -> None:
        bus = FakeBus()
        self.assertFalse(bus.started_running)
        bus.run_forever()
        self.assertTrue(bus.started_running)

    def test_run_in_thread(self) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        self.assertTrue(bus.started_running)

    def test_on_and_emit(self) -> None:
        bus = FakeBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.on("test.event", handler)
        msg = FakeMessage("test.event", {"hello": "world"})
        bus.emit(msg)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].data["hello"], "world")

    def test_once(self) -> None:
        bus = FakeBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.once("once.event", handler)
        msg = FakeMessage("once.event")
        bus.emit(msg)
        bus.emit(msg)
        self.assertEqual(len(received), 1)

    def test_remove_listener(self) -> None:
        bus = FakeBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.on("test.remove", handler)
        bus.remove("test.remove", handler)
        bus.emit(FakeMessage("test.remove"))
        self.assertEqual(len(received), 0)

    def test_remove_all_listeners(self) -> None:
        bus = FakeBus()
        received = []

        bus.on("event", lambda m: received.append(m))
        bus.on("event", lambda m: received.append(m))
        bus.remove_all_listeners("event")
        bus.emit(FakeMessage("event"))
        self.assertEqual(len(received), 0)

    def test_wait_for_message(self) -> None:
        bus = FakeBus()

        import threading
        def send_later():
            import time
            time.sleep(0.05)
            bus.emit(FakeMessage("delayed.event", {"val": 99}))

        t = threading.Thread(target=send_later)
        t.start()
        msg = bus.wait_for_message("delayed.event", timeout=2.0)
        t.join()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.data["val"], 99)

    def test_wait_for_message_timeout(self) -> None:
        bus = FakeBus()
        msg = bus.wait_for_message("never.comes", timeout=0.05)
        self.assertIsNone(msg)

    def test_wait_for_response(self) -> None:
        bus = FakeBus()

        def auto_reply(msg):
            bus.emit(msg.response({"answer": 42}))

        bus.on("question", auto_reply)
        request = FakeMessage("question", {"q": "?"})
        response = bus.wait_for_response(request, timeout=2.0)
        self.assertIsNotNone(response)
        self.assertEqual(response.data["answer"], 42)

    def test_create_client_returns_self(self) -> None:
        bus = FakeBus()
        self.assertIs(bus.create_client(), bus)

    def test_close(self) -> None:
        bus = FakeBus()
        bus.close()  # Should not raise

    def test_on_error_does_not_raise(self) -> None:
        bus = FakeBus()
        bus.on_error(Exception("test error"))  # Should not raise


if __name__ == "__main__":
    unittest.main()
