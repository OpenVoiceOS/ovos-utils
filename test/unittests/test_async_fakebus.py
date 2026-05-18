# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
"""Tests for AsyncFakeBus.

Mirrors test_fakebus.py shape but exercises the async surface
(connect / close / emit / wait_for_message / wait_for_response) plus
the sync handler-registration contract that matches
AsyncMessageBusClient.
"""
import asyncio
import unittest

from ovos_utils.fakebus import AsyncFakeBus, FakeMessage


def _run(coro):
    """Tiny helper so we can use plain unittest.TestCase."""
    return asyncio.run(coro)


class TestAsyncFakeBusLifecycle(unittest.TestCase):
    def test_constructs_connected(self):
        bus = AsyncFakeBus()
        self.assertTrue(bus.connected_event.is_set())

    def test_session_id_from_kwargs(self):
        class _Sess:
            session_id = "from-kwarg"
        bus = AsyncFakeBus(session=_Sess())
        self.assertEqual(bus.session_id, "from-kwarg")

    def test_connect_is_noop_but_sets_event(self):
        bus = AsyncFakeBus()
        bus.connected_event.clear()
        _run(bus.connect())
        self.assertTrue(bus.connected_event.is_set())
        self.assertTrue(bus.started_running)

    def test_close_clears_connected_event(self):
        bus = AsyncFakeBus()
        self.assertTrue(bus.connected_event.is_set())
        _run(bus.close())
        self.assertFalse(bus.connected_event.is_set())


class TestAsyncFakeBusHandlerRegistration(unittest.TestCase):
    def test_on_then_emit_dispatches(self):
        bus = AsyncFakeBus()
        seen = []
        bus.on("hello", lambda m: seen.append(m))
        _run(bus.emit(FakeMessage("hello", {"x": 1})))
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].msg_type, "hello")
        self.assertEqual(seen[0].data["x"], 1)

    def test_once_fires_only_once(self):
        bus = AsyncFakeBus()
        seen = []
        bus.once("evt", lambda m: seen.append(m))
        _run(bus.emit(FakeMessage("evt")))
        _run(bus.emit(FakeMessage("evt")))
        self.assertEqual(len(seen), 1)

    def test_remove_handler(self):
        bus = AsyncFakeBus()
        seen = []

        def cb(m):
            seen.append(m)

        bus.on("evt", cb)
        bus.remove("evt", cb)
        _run(bus.emit(FakeMessage("evt")))
        self.assertEqual(seen, [])

    def test_remove_all_listeners(self):
        bus = AsyncFakeBus()
        bus.on("evt", lambda m: None)
        bus.on("evt", lambda m: None)
        bus.remove_all_listeners("evt")
        self.assertEqual(bus.ee.listeners("evt"), [])

    def test_remove_unknown_handler_does_not_raise(self):
        bus = AsyncFakeBus()
        # not registered → silent
        bus.remove("evt", lambda m: None)


class TestAsyncFakeBusEmit(unittest.TestCase):
    def test_emit_injects_session_context_when_missing(self):
        bus = AsyncFakeBus()
        msg = FakeMessage("hello", {})
        self.assertNotIn("session", msg.context)
        _run(bus.emit(msg))
        self.assertIn("session", msg.context)

    def test_emit_dispatches_raw_message_event(self):
        bus = AsyncFakeBus()
        raws = []
        bus.on("message", lambda raw: raws.append(raw))
        _run(bus.emit(FakeMessage("hello")))
        self.assertEqual(len(raws), 1)
        self.assertIn("hello", raws[0])


class TestAsyncFakeBusWaitForMessage(unittest.TestCase):
    def test_returns_matched_message_emitted_concurrently(self):
        bus = AsyncFakeBus()

        async def scenario():
            async def feed():
                await asyncio.sleep(0.02)
                await bus.emit(FakeMessage("ping", {"flood_id": "x"}))
            asyncio.create_task(feed())
            got = await bus.wait_for_message("ping", timeout=1.0)
            return got

        got = _run(scenario())
        self.assertIsNotNone(got)
        self.assertEqual(got.msg_type, "ping")

    def test_returns_none_on_timeout(self):
        bus = AsyncFakeBus()

        async def scenario():
            return await bus.wait_for_message("never", timeout=0.05)

        self.assertIsNone(_run(scenario()))


class TestAsyncFakeBusWaitForResponse(unittest.TestCase):
    def test_default_reply_type_is_msg_type_response(self):
        bus = AsyncFakeBus()

        async def scenario():
            # echo the request as <type>.response when the request arrives
            def echo(m):
                # synchronous dispatch — fire the reply inline
                # cannot await here; schedule on the loop instead
                asyncio.create_task(
                    bus.emit(FakeMessage(m.msg_type + ".response",
                                         {"echoed": m.data})))
            bus.on("ask", echo)
            return await bus.wait_for_response(
                FakeMessage("ask", {"q": 1}), timeout=1.0,
            )

        reply = _run(scenario())
        self.assertIsNotNone(reply)
        self.assertEqual(reply.msg_type, "ask.response")
        self.assertEqual(reply.data["echoed"], {"q": 1})

    def test_explicit_reply_type(self):
        bus = AsyncFakeBus()

        async def scenario():
            def respond(m):
                asyncio.create_task(bus.emit(FakeMessage("pong")))
            bus.on("ping", respond)
            return await bus.wait_for_response(
                FakeMessage("ping"), reply_type="pong", timeout=1.0,
            )

        reply = _run(scenario())
        self.assertIsNotNone(reply)
        self.assertEqual(reply.msg_type, "pong")

    def test_returns_none_on_timeout(self):
        bus = AsyncFakeBus()

        async def scenario():
            return await bus.wait_for_response(
                FakeMessage("never"), timeout=0.05,
            )

        self.assertIsNone(_run(scenario()))


class TestAsyncFakeBusCompatShims(unittest.TestCase):
    def test_create_client_returns_self(self):
        bus = AsyncFakeBus()
        self.assertIs(bus.create_client(), bus)

    def test_run_forever_flips_started_running(self):
        bus = AsyncFakeBus()
        bus.started_running = False
        bus.run_forever()
        self.assertTrue(bus.started_running)

    def test_run_in_thread_alias(self):
        bus = AsyncFakeBus()
        bus.started_running = False
        bus.run_in_thread()
        self.assertTrue(bus.started_running)


if __name__ == "__main__":
    unittest.main()
