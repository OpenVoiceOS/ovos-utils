# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import time
import unittest
from ovos_utils.metrics import Stopwatch


class MetricsTests(unittest.TestCase):

    def test_stopwatch_simple(self):
        sleep_time = 1.00
        stopwatch = Stopwatch()
        with stopwatch:
            time.sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

    def test_stopwatch_reuse(self):
        sleep_time = 0.5
        stopwatch = Stopwatch()
        with stopwatch:
            time.sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

        with stopwatch:
            time.sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

        with stopwatch:
            time.sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

    def test_stopwatch_no_start(self):
        stopwatch = Stopwatch()
        elapsed = stopwatch.stop()
        self.assertEqual(elapsed, 0.0)

    def test_start_and_stop(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.1)
        elapsed = sw.stop()
        self.assertGreater(elapsed, 0.0)
        self.assertIsNone(sw.timestamp)  # stopped
        self.assertAlmostEqual(elapsed, 0.1, delta=0.05)

    def test_lap(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.1)
        lap1 = sw.lap()
        time.sleep(0.1)
        lap2 = sw.lap()
        self.assertGreater(lap1, 0.0)
        self.assertGreater(lap2, 0.0)

    def test_delta_when_running(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        delta = sw.delta
        self.assertGreater(delta, 0.0)

    def test_delta_when_stopped(self):
        sw = Stopwatch()
        # Not started — delta should be 0
        self.assertEqual(sw.delta, 0)

    def test_delta_after_stop(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        sw.stop()
        delta = sw.delta
        # After stop, timestamp is None, so delta returns self.time
        self.assertGreater(delta, 0.0)

    def test_str_not_started(self):
        sw = Stopwatch()
        self.assertEqual(str(sw), "Not started")

    def test_str_running(self):
        sw = Stopwatch()
        sw.start()
        s = str(sw)
        # Should be a numeric string (time elapsed)
        self.assertNotEqual(s, "Not started")
        float(s)  # Should be parseable as float

    def test_str_stopped(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        sw.stop()
        # After stop, timestamp is None, str returns "Not started" unless time set
        # Based on implementation: if timestamp is set returns time, else "Not started"
        # After stop: timestamp = None, so "Not started"
        s = str(sw)
        self.assertEqual(s, "Not started")

    def test_context_manager_sets_time(self):
        sw = Stopwatch()
        with sw:
            time.sleep(0.05)
        self.assertIsNotNone(sw.time)
        self.assertGreater(sw.time, 0.0)

    def test_initial_state(self):
        sw = Stopwatch()
        self.assertIsNone(sw.timestamp)
        self.assertIsNone(sw.time)

    def test_start_resets_time(self):
        sw = Stopwatch()
        sw.start()
        time.sleep(0.05)
        sw.stop()
        old_time = sw.time
        sw.start()
        self.assertIsNone(sw.time)  # reset on start


if __name__ == "__main__":
    unittest.main()
