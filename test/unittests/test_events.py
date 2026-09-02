import inspect
import unittest
import datetime

from os.path import join, dirname
from threading import Event
from time import time
from unittest.mock import Mock


from ovos_utils.fakebus import FakeBus, FakeMessage as Message


class TestEvents(unittest.TestCase):
    bus = FakeBus()
    test_schedule = join(dirname(__file__), "schedule.json")

    def test_unmunge_message(self):
        from ovos_utils.events import unmunge_message
        test_message = Message("test", {"TESTSKILLTESTSKILL": True,
                                        "TESTSKILLdata": "nothing"})
        self.assertEqual(unmunge_message(test_message, "OtherSkill"),
                         test_message)
        unmunged = unmunge_message(test_message, "TESTSKILL")
        self.assertEqual(unmunged.msg_type, test_message.msg_type)
        self.assertEqual(unmunged.data, {"TESTSKILL": True,
                                         "data": "nothing"})

    def test_get_handler_name(self):
        from ovos_utils.events import get_handler_name

        class Test:
            def __init__(self):
                self.name = "test"

            def handler(self, msg):
                print(f"{self.name}: {msg}")

        self.assertEqual(get_handler_name(Test().handler), "test.handler")

        def handler():
            print("")

        self.assertEqual(get_handler_name(handler), "handler")

    def test_create_wrapper(self):
        from ovos_utils.events import create_wrapper
        # TODO

    def test_create_basic_wrapper(self):
        from ovos_utils.events import create_basic_wrapper

        # Test invalid call to wrapped method
        wrapped = create_basic_wrapper(Mock())
        with self.assertRaises(TypeError):
            wrapped()

        test_message = Message("test")

        # Test simple wrapper, no args
        call_count = 0

        def _no_args():
            nonlocal call_count
            call_count += 1

        wrapped = create_basic_wrapper(_no_args)
        self.assertEqual(call_count, 0)
        wrapped(test_message)
        self.assertEqual(call_count, 1)

        # Test wrapper with message arg
        called_with = None

        def _with_arg(msg):
            nonlocal called_with
            called_with = msg

        wrapped = create_basic_wrapper(_with_arg)
        self.assertIsNone(called_with)
        wrapped(test_message)
        self.assertEqual(called_with, test_message)

        # Test error callback
        def _too_many_args(arg1, arg2):
            pass

        def _internal_exception():
            raise RuntimeError

        error_handler = Mock()
        wrapped = create_basic_wrapper(_too_many_args, error_handler)
        wrapped(test_message)
        error_handler.assert_called_once()
        self.assertIsInstance(error_handler.call_args[0][0], TypeError)

        error_handler.reset_mock()
        wrapped = create_basic_wrapper(_internal_exception, error_handler)
        wrapped(test_message)
        error_handler.assert_called_once()
        self.assertIsInstance(error_handler.call_args[0][0], RuntimeError)

        # Test wrapper with methods
        class WrapperContainer:
            no_args_calls = 0
            with_args_calls = []

            def no_args(self):
                self.no_args_calls += 1

            def with_args(self, message):
                self.with_args_calls.append(message)

            def call_wrapped_functions(self, message, with_args: bool):
                if with_args:
                    create_basic_wrapper(self.with_args)(message)
                else:
                    create_basic_wrapper(self.no_args)(message)

        test_class = WrapperContainer()
        test_class.call_wrapped_functions(test_message, False)
        self.assertEqual(test_class.no_args_calls, 1)
        self.assertEqual(test_class.with_args_calls, [])
        test_class.call_wrapped_functions(test_message, True)
        self.assertEqual(test_class.no_args_calls, 1)
        self.assertEqual(test_class.with_args_calls, [test_message])

    def test_event_container(self):
        from ovos_utils.events import EventContainer
        container = EventContainer()
        self.assertIsInstance(container.bus, FakeBus)
        self.assertIsInstance(container.events, list)

        # Test set bus
        bus = FakeBus()
        container.set_bus(bus)
        self.assertEqual(bus, container.bus)

        # Add simple
        handler = Mock()
        event_name = "test_event"
        container.add(event_name, handler)
        self.assertEqual(len(bus.ee.listeners(event_name)), 1)
        self.assertEqual(container.events, [(event_name, handler)])

        # Add second handler for same event
        handler2 = Mock()
        event_name = "test_event"
        container.add(event_name, handler2)
        self.assertEqual(len(bus.ee.listeners(event_name)), 2)
        self.assertEqual(container.events, [(event_name, handler),
                                            (event_name, handler2)])

        # Add handler with once_wrapper
        container.add("once_event", handler, once=True)
        self.assertEqual(len(bus.ee.listeners("once_event")), 1)
        new_event = container.events[-1]
        self.assertEqual(new_event[0], "once_event")
        self.assertNotEqual(new_event[1], handler)
        self.assertEqual(len(inspect.signature(new_event[1]).parameters), 1)

        # Test iterate events
        for event in container:
            self.assertIn(event, container.events)

        # Remove simple
        self.assertTrue(container.remove("once_event"))
        self.assertEqual(bus.ee.listeners("once_event"), [])

        # Remove multiple handlers
        self.assertTrue(container.remove(event_name))
        self.assertEqual(bus.ee.listeners(event_name), [])

        # Test remove no listeners
        self.assertFalse(container.remove(event_name))
        self.assertFalse(container.remove(None))
        self.assertEqual(container.events, [])

        # Test clear
        container.add(event_name, handler)
        container.clear()
        self.assertEqual(container.events, [])
        self.assertEqual(bus.ee.listeners(event_name), [])


class TestCreateWrapper(unittest.TestCase):
    """Tests for create_wrapper covering lines 71-92."""

    def test_create_wrapper_calls_handler_no_args(self) -> None:
        """create_wrapper should call a zero-argument handler."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        calls = []

        def handler():
            calls.append(True)

        wrapped = create_wrapper(handler, "skill_id", None, None, None)
        wrapped(FakeMessage("test"))
        self.assertEqual(len(calls), 1)

    def test_create_wrapper_calls_handler_with_message(self) -> None:
        """create_wrapper should pass message to a handler that accepts one."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        received = []

        def handler(msg):
            received.append(msg)

        msg = FakeMessage("test.msg")
        wrapped = create_wrapper(handler, "skill_id", None, None, None)
        wrapped(msg)
        self.assertEqual(len(received), 1)

    def test_create_wrapper_calls_on_start(self) -> None:
        """create_wrapper should call on_start before calling handler."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        order = []

        def on_start(msg):
            order.append("start")

        def handler(msg):
            order.append("handler")

        wrapped = create_wrapper(handler, "skill_id", on_start, None, None)
        wrapped(FakeMessage("test"))
        self.assertEqual(order, ["start", "handler"])

    def test_create_wrapper_calls_on_end(self) -> None:
        """create_wrapper should call on_end in finally block."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        ended = []

        def on_end(msg):
            ended.append(True)

        def handler(msg):
            pass

        wrapped = create_wrapper(handler, "skill_id", None, on_end, None)
        wrapped(FakeMessage("test"))
        self.assertTrue(ended)

    def test_create_wrapper_calls_on_error_one_arg(self) -> None:
        """create_wrapper should call on_error(e) for single-arg error callback."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        errors = []

        def handler(msg):
            raise RuntimeError("boom")

        def on_error(e):
            errors.append(e)

        wrapped = create_wrapper(handler, "skill_id", None, None, on_error)
        wrapped(FakeMessage("test"))
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)

    def test_create_wrapper_calls_on_error_two_args(self) -> None:
        """create_wrapper should call on_error(e, msg) for two-arg error callback."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        errors = []

        def handler(msg):
            raise ValueError("bad")

        def on_error(e, msg):
            errors.append((e, msg))

        wrapped = create_wrapper(handler, "skill_id", None, None, on_error)
        wrapped(FakeMessage("test"))
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0][0], ValueError)

    def test_create_wrapper_on_end_called_even_on_error(self) -> None:
        """create_wrapper on_end should be called even when handler raises."""
        from ovos_utils.events import create_wrapper
        from ovos_utils.fakebus import FakeMessage
        ended = []

        def handler(msg):
            raise Exception("error")

        def on_end(msg):
            ended.append(True)

        wrapped = create_wrapper(handler, "skill_id", None, on_end, None)
        wrapped(FakeMessage("test"))
        self.assertTrue(ended)


class TestEventContainerOnce(unittest.TestCase):
    """Tests for EventContainer once-handler path (lines 154-155)."""

    def test_once_handler_invokes_and_removes(self) -> None:
        """once_wrapper should invoke the handler and remove the event."""
        from ovos_utils.events import EventContainer
        from ovos_utils.fakebus import FakeBus, FakeMessage
        bus = FakeBus()
        container = EventContainer(bus)
        called = []

        def handler(msg):
            called.append(msg)

        container.add("once.event", handler, once=True)
        bus.emit(FakeMessage("once.event"))
        self.assertEqual(len(called), 1)
        # After once fires, the event should be removed
        self.assertEqual(container.events, [])

    def test_remove_error_logged(self) -> None:
        """EventContainer.remove should handle ValueError gracefully."""
        from ovos_utils.events import EventContainer
        from ovos_utils.fakebus import FakeBus

        # Subclass list to override remove so it always raises ValueError
        class BrokenList(list):
            def remove(self, item):
                raise ValueError("forced")

        bus = FakeBus()
        container = EventContainer(bus)
        broken = BrokenList()
        broken.append(("bad.event", lambda m: None))
        container.events = broken
        # Should not raise despite the ValueError
        result = container.remove("bad.event")
        self.assertTrue(result)


