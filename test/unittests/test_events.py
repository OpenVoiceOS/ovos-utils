import inspect
import unittest
import datetime

from os.path import join, dirname
from threading import Event
from time import time
from unittest.mock import Mock

from ovos_utils.fakebus import FakeBus, Message


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
        self.assertNotEquals(new_event[1], handler)
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


class TestEventSchedulerInterface(unittest.TestCase):
    from ovos_utils.events import EventSchedulerInterface
    bus = FakeBus()
    interface = EventSchedulerInterface(bus=bus, name="test")

    def test_00_init(self):
        from ovos_utils.events import EventContainer
        self.assertEqual(self.interface.bus, self.bus)
        self.assertIsInstance(self.interface.skill_id, str)
        self.assertIsInstance(self.interface.events, EventContainer)
        self.assertEqual(self.interface.events.bus, self.bus)
        self.assertEqual(self.interface.scheduled_repeats, list())

        # Deprecated properties
        self.assertEqual(self.interface.sched_id, self.interface.skill_id)
        self.assertEqual(self.interface.name, self.interface.skill_id)

    def test_set_bus(self):
        bus = FakeBus()
        interface = self.EventSchedulerInterface(bus=bus, name="test")
        interface.set_bus(self.bus)
        self.assertEqual(interface.bus, self.bus)
        self.assertEqual(interface.events.bus, self.bus)

    def test_set_id(self):
        test_id = "testing"
        self.interface.set_id(test_id)
        self.assertEqual(self.interface.skill_id, test_id)

    def test_get_source_message(self):
        message = self.interface._get_source_message()
        self.assertIsInstance(message, Message)
        self.assertEqual(message.context['skill_id'], self.interface.skill_id)

    def test_create_unique_name(self):
        test = "handler"
        self.assertEqual(self.interface._create_unique_name(test),
                         f"{self.interface.skill_id}:{test}")

        self.assertEqual(self.interface._create_unique_name(""),
                         f"{self.interface.skill_id}:")
        self.assertEqual(self.interface._create_unique_name(None),
                         f"{self.interface.skill_id}:")

    def test__schedule_event(self):
        # Test invalid time
        with self.assertRaises(ValueError):
            self.interface._schedule_event(Mock(), -10, None, None)
        with self.assertRaises(TypeError):
            self.interface._schedule_event(Mock(), None, None, None)

        handle_schedule_event = Mock()
        self.bus.on("mycroft.scheduler.schedule_event", handle_schedule_event)

        self.bus.remove("mycroft.scheduler.schedule_event", handle_schedule_event)

        now_time = datetime.datetime.now(datetime.timezone.utc)
        self.assertAlmostEqual(now_time.timestamp(), time(), 0)
        event_time_tzaware = now_time + datetime.timedelta(hours=1)
        event_time_seconds = event_time_tzaware.timestamp()
        event_time_tznaive = datetime.datetime.fromtimestamp(event_time_seconds)

        scheduled = Event()
        messages = list()

        def on_schedule(msg):
            nonlocal messages
            messages.append(msg)
            scheduled.set()

        self.bus.on('mycroft.scheduler.schedule_event', on_schedule)

        name = None
        context = {"test": time()}
        data = {"test": True}
        callback = Mock()
        callback.__name__ = "test"

        # Schedule TZ Aware
        scheduled.clear()
        self.interface._schedule_event(callback, event_time_tzaware, data, name,
                                       context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 1)

        # Schedule TZ Naive
        scheduled.clear()
        self.interface._schedule_event(callback, event_time_tznaive, data, name,
                                       context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 2)

        # Schedule duration
        self.interface._schedule_event(callback, event_time_seconds -
                                       datetime.datetime.now().timestamp(),
                                       data, name, context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 3)

        # Schedule repeating
        # TODO

        for event in messages:
            self.assertIsInstance(event, Message)
            self.assertEqual(event.context['test'], context['test'])
            self.assertEqual(event.context['skill_id'], self.interface.skill_id)
            self.assertEqual(event.data['data'], data)
            self.assertIsInstance(event.data['event'], str)
            self.assertIsNone(event.data['repeat'])
            self.assertAlmostEqual(event.data['time'], event_time_seconds, 0)

        self.bus.remove('mycroft.scheduler.schedule_event', on_schedule)

    def test_schedule_event(self):
        real_schedule = self.interface._schedule_event
        self.interface._schedule_event = Mock()
        callback = Mock()

        self.interface.schedule_event(callback, -3.0)
        self.interface._schedule_event.assert_called_with(callback, -3.0, None,
                                                          None, context=None)
        self.interface._schedule_event = real_schedule

    def test_schedule_repeating_event(self):
        real_schedule = self.interface._schedule_event
        self.interface._schedule_event = Mock()
        callback = Mock()
        callback.__name__ = "repeat_test"

        # Schedule no name event with no time
        self.interface.schedule_repeating_event(callback, None, 30)
        self.interface._schedule_event.assert_called_once()

        # Schedule with name and time
        event_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        self.interface.schedule_repeating_event(callback, event_time, 30,
                                                name=callback.__name__)
        self.interface._schedule_event.assert_called_with(callback, event_time,
                                                          None,
                                                          callback.__name__,
                                                          30, None)

        # Already scheduled, don't do it again
        self.interface._schedule_event.reset_mock()
        self.interface.scheduled_repeats.append(callback.__name__)
        self.interface.schedule_repeating_event(callback, None, 30,
                                                name=callback.__name__)
        self.interface._schedule_event.assert_not_called()

        self.interface._schedule_event = real_schedule

    def test_update_scheduled_event(self):
        # TODO
        pass

    def test_cancel_scheduled_event(self):
        # TODO
        pass

    def test_get_scheduled_event_status(self):
        # TODO
        pass

    def test_cancel_all_repeating_events(self):
        # TODO
        pass

    def test_shutdown(self):
        real_cancel_repeating = self.interface.cancel_all_repeating_events
        real_clear = self.interface.events.clear
        self.interface.cancel_all_repeating_events = Mock()
        self.interface.events.clear = Mock()

        self.interface.shutdown()
        self.interface.cancel_all_repeating_events.assert_called_once()
        self.interface.events.clear.assert_called_once()

        self.interface.cancel_all_repeating_events = real_cancel_repeating
        self.interface.events.clear = real_clear
