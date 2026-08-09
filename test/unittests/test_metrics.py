# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import time
import unittest
from unittest.mock import patch

from ovos_utils.metrics import LatencyHistogram, Stopwatch


class MetricsTests(unittest.TestCase):
    def test_latency_histogram_snapshot(self):
        histogram = LatencyHistogram("handler_ms", buckets_ms=(1, 5, 10))
        histogram.observe_ms(0.5)
        histogram.observe_ms(5)
        histogram.observe_ms(12)

        self.assertEqual(
            histogram.snapshot(),
            {
                "name": "handler_ms",
                "count": 3,
                "sum_ms": 17.5,
                "buckets": {
                    "le_1": 1,
                    "le_5": 2,
                    "le_10": 2,
                    "inf": 3,
                },
            },
        )

    def test_latency_histogram_rejects_malformed_values(self):
        with self.assertRaises(ValueError):
            LatencyHistogram("duplicate_ms", buckets_ms=(1, 1))
        with self.assertRaises(ValueError):
            LatencyHistogram("negative_ms", buckets_ms=(-1, 1))
        with self.assertRaises(ValueError):
            LatencyHistogram("infinite_ms", buckets_ms=(1, float("inf")))

        histogram = LatencyHistogram("handler_ms")
        with self.assertRaises(TypeError):
            histogram.observe_ms(True)
        with self.assertRaises(ValueError):
            histogram.observe_ms(float("nan"))
        histogram.observe_ms(-1)
        self.assertEqual(histogram.snapshot()["sum_ms"], 0)

    @patch("ovos_utils.metrics.time.monotonic")
    def test_latency_histogram_pauses_and_finishes_once(self, monotonic):
        monotonic.side_effect = (0.0, 0.1, 1.0, 1.2)
        histogram = LatencyHistogram("selection_ms", buckets_ms=(250, 500))

        with histogram.measure() as measurement:
            measurement.pause()
            measurement.resume()
        measurement.finish()

        snapshot = histogram.snapshot()
        self.assertEqual(snapshot["count"], 1)
        self.assertAlmostEqual(snapshot["sum_ms"], 300)
        self.assertEqual(
            snapshot["buckets"],
            {
                "le_250": 0,
                "le_500": 1,
                "inf": 1,
            },
        )

    @patch("ovos_utils.metrics.time.monotonic", side_effect=(2.0, 2.025))
    def test_latency_histogram_records_exceptional_exit(self, _monotonic):
        histogram = LatencyHistogram("handler_ms", buckets_ms=(25, 50))

        with self.assertRaisesRegex(RuntimeError, "handler failed"):
            with histogram.measure():
                raise RuntimeError("handler failed")

        self.assertEqual(histogram.snapshot()["count"], 1)
        self.assertAlmostEqual(histogram.snapshot()["sum_ms"], 25)

    @patch("ovos_utils.metrics.time.monotonic", side_effect=(4.0, 4.01))
    def test_latency_histogram_timed_preserves_metadata(self, _monotonic):
        histogram = LatencyHistogram("decorated_ms", buckets_ms=(10, 25))

        @histogram.timed
        def measured(value):
            """Return the measured value."""
            return value

        self.assertEqual(measured("ok"), "ok")
        self.assertEqual(measured.__name__, "measured")
        self.assertEqual(histogram.snapshot()["count"], 1)
        self.assertAlmostEqual(histogram.snapshot()["sum_ms"], 10)

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
        sw.start()
        self.assertIsNone(sw.time)  # reset on start


if __name__ == "__main__":
    unittest.main()
