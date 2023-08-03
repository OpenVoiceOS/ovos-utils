import unittest
import datetime

from os.path import join, dirname
from threading import Event
from time import time
from unittest.mock import Mock

from ovos_utils.messagebus import FakeBus, Message


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
        # TODO

    def test_event_scheduler_interface(self):
        from ovos_utils.events import EventSchedulerInterface, EventContainer
        interface = EventSchedulerInterface(bus=self.bus, name="test")
        self.assertEqual(interface.bus, self.bus)
        self.assertIsInstance(interface.skill_id, str)
        test_id = "testing"
        interface.set_id(test_id)
        self.assertEqual(interface.skill_id, test_id)
        self.assertIsInstance(interface.events, EventContainer)
        self.assertEqual(interface.events.bus, self.bus)
        self.assertEqual(interface.scheduled_repeats, list())

        # Deprecated properties
        self.assertEqual(interface.sched_id, interface.skill_id)
        self.assertEqual(interface.name, interface.skill_id)

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

        context = {
            "test": time()
        }

        data = {
            "test": True
        }

        callback = Mock()
        callback.__name__ = "test"

        # Schedule TZ Aware
        scheduled.clear()
        interface.schedule_event(callback, event_time_tzaware, data,
                                 context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 1)

        # Schedule TZ Naive
        scheduled.clear()
        interface.schedule_event(callback, event_time_tznaive, data,
                                 context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 2)

        # Schedule duration
        interface.schedule_event(callback, event_time_seconds -
                                 datetime.datetime.now().timestamp(),
                                 data, context=context)
        self.assertTrue(scheduled.wait(2))
        self.assertEqual(len(messages), 3)

        for event in messages:
            self.assertIsInstance(event, Message)
            self.assertEqual(event.context, context)
            self.assertEqual(event.data['data'], data)
            self.assertIsInstance(event.data['event'], str)
            self.assertIsNone(event.data['repeat'])
            self.assertAlmostEqual(event.data['time'], event_time_seconds, 0)

        # Schedule invalid
        with self.assertRaises(ValueError):
            interface.schedule_event(callback, -3.0)

        # TODO: Test Repeating, Update, Cancel, Get Status

        interface.shutdown()
        self.assertEqual(interface.events.events, list())
