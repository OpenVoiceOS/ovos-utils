"""
    Test cases regarding the event scheduler.
"""

import unittest

import pytest

from ovos_utils.events import EventSchedulerInterface
from ovos_utils.fakebus import FakeBus


@pytest.mark.filterwarnings("ignore:EventSchedulerInterface moved to ovos_bus_client:DeprecationWarning")
class TestEventSchedulerInterface(unittest.TestCase):
    def test_shutdown(self):
        def f(message):
            print('TEST FUNC')

        es = EventSchedulerInterface('tester')
        es.set_bus(FakeBus())
        es.set_id('id')

        # Schedule a repeating event
        es.schedule_repeating_event(f, None, 10, name='f')
        self.assertTrue(len(es.bus.ee._events.get('id:f', [])) == 1)

        es.shutdown()
        # Check that the reference to the function has been removed from the
        # bus emitter
        self.assertTrue(len(es.bus.ee._events.get('id:f', [])) == 0)
