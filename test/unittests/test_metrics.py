
import unittest
from time import sleep
from ovos_utils.metrics import Stopwatch


class MetricsTests(unittest.TestCase):

    def test_stopwatch_simple(self):
        sleep_time = 1.00
        stopwatch = Stopwatch()
        with stopwatch:
            sleep(sleep_time)
        self.assertLess(abs(stopwatch.time - sleep_time), 2)

    def test_stopwatch_reuse(self):
        sleep_time = 0.5
        stopwatch = Stopwatch()
        with stopwatch:
            sleep(sleep_time)
        self.assertLess(abs(stopwatch.time - sleep_time), 0.01)

        with stopwatch:
            sleep(sleep_time)
        self.assertLess(abs(stopwatch.time - sleep_time), 0.01) 

        with stopwatch:
            sleep(sleep_time)
        self.assertLess(abs(stopwatch.time - sleep_time), 0.01) 

    def test_stopwatch_no_start(self):
        stopwatch = Stopwatch()
        time = stopwatch.stop()
        self.assertEqual(time, 0.0)
