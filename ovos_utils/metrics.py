import math
import os
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from functools import wraps
from threading import Lock
from typing import Any, Optional, TypeVar


DEFAULT_LATENCY_BUCKETS_MS = (
    1.0,
    2.5,
    5.0,
    10.0,
    25.0,
    50.0,
    100.0,
    250.0,
    500.0,
    1_000.0,
    2_500.0,
    5_000.0,
    10_000.0,
    30_000.0,
)

#: The package declares requires-python >=3.9, so this module stays on 3.9
#: syntax: no typing.ParamSpec (3.10) and no zip(strict=) (3.10). The
#: decorator is typed on its return value only, which is what callers see.
R = TypeVar("R")

#: Metrics are opt-in. Recording is switched on by the same variable that
#: enables the scrape endpoint, so a process that never asked for metrics does
#: not accumulate counters nobody can read.
METRICS_ENABLED_ENV = "OVOS_METRICS_ENABLED"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

#: Reading the environment on every observation would put a syscall on hot
#: paths, so the answer is resolved once and cached.
#: :func:`reset_metrics_recording_cache` lets tests flip the switch in-process.
_RECORDING_ENABLED: Optional[bool] = None


def metrics_enabled() -> bool:
    """Whether the opt-in metrics switch (``OVOS_METRICS_ENABLED``) is on."""
    return os.getenv(METRICS_ENABLED_ENV, "false").strip().lower() in _TRUE_VALUES


def metrics_recording_enabled() -> bool:
    """Cached :func:`metrics_enabled`, for observation hot paths."""
    global _RECORDING_ENABLED
    if _RECORDING_ENABLED is None:
        _RECORDING_ENABLED = metrics_enabled()
    return _RECORDING_ENABLED


def reset_metrics_recording_cache() -> None:
    """Forget the cached answer; for tests that change the environment."""
    global _RECORDING_ENABLED
    _RECORDING_ENABLED = None




class LatencyMeasurement:
    """A pausable, single-observation monotonic latency measurement."""

    def __init__(self, histogram: "LatencyHistogram") -> None:
        self._histogram = histogram
        self._started = time.monotonic()
        self._elapsed_ms = 0.0
        self._running = True
        self._finished = False
        self._lock = Lock()

    def pause(self) -> None:
        """Exclude subsequent time until :meth:`resume` is called."""
        with self._lock:
            if self._running and not self._finished:
                self._elapsed_ms += (time.monotonic() - self._started) * 1_000
                self._running = False

    def resume(self) -> None:
        """Resume measuring after a pause."""
        with self._lock:
            if not self._running and not self._finished:
                self._started = time.monotonic()
                self._running = True

    def finish(self) -> None:
        """Record accumulated active time exactly once."""
        with self._lock:
            if self._finished:
                return
            if self._running:
                self._elapsed_ms += (
                    time.monotonic() - self._started
                ) * 1_000
                self._running = False
            self._finished = True
            elapsed_ms = self._elapsed_ms
        self._histogram.observe_ms(elapsed_ms)


class LatencyHistogram:
    """Thread-safe cumulative latency histogram with fixed buckets."""

    def __init__(
        self,
        name: str,
        *,
        buckets_ms: Iterable[float] = DEFAULT_LATENCY_BUCKETS_MS,
        enabled: Optional[Callable[[], bool]] = None,
    ) -> None:
        """
        Args:
            name: metric name; a trailing ``_ms`` is exported as ``_seconds``.
            buckets_ms: ascending upper bounds in milliseconds.
            enabled: zero-argument callable deciding whether observations are
                recorded. Defaults to :func:`metrics_recording_enabled`, so
                nothing is accumulated unless metrics were switched on.
        """
        bounds = tuple(sorted(float(value) for value in buckets_ms))
        if any(not math.isfinite(value) or value < 0 for value in bounds):
            raise ValueError("buckets_ms must be finite and non-negative")
        if any(left == right for left, right in zip(bounds, bounds[1:])):
            raise ValueError("buckets_ms must not contain duplicates")
        self.name = name
        self._enabled = enabled or metrics_recording_enabled
        self._bounds = bounds
        self._buckets = [0] * len(bounds)
        self._count = 0
        self._sum_ms = 0.0
        self._lock = Lock()

    def observe_ms(self, elapsed_ms: float) -> None:
        """Record one finite, non-negative duration in milliseconds.

        A no-op while recording is disabled.
        """
        if not self._enabled():
            return
        if isinstance(elapsed_ms, bool):
            raise TypeError("elapsed_ms must be numeric")
        value = float(elapsed_ms)
        if not math.isfinite(value):
            raise ValueError("elapsed_ms must be finite")
        value = max(0.0, value)
        with self._lock:
            self._count += 1
            self._sum_ms += value
            for index, bound in enumerate(self._bounds):
                if value <= bound:
                    self._buckets[index] += 1

    @contextmanager
    def measure(self) -> Iterator[LatencyMeasurement]:
        """Record active enclosed time, including exceptional exits."""
        measurement = LatencyMeasurement(self)
        try:
            yield measurement
        finally:
            measurement.finish()

    def timed(self, function: Callable[..., R]) -> Callable[..., R]:
        """Decorate a synchronous function with this histogram."""

        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> R:
            with self.measure():
                return function(*args, **kwargs)

        return wrapped

    def snapshot(self) -> Mapping[str, Any]:
        """Return a detached, JSON-friendly cumulative snapshot."""
        with self._lock:
            # zip(strict=) is 3.10+; the invariant it guarded still holds
            # by construction (_buckets is sized from _bounds), so assert it
            # rather than silently truncating if that ever changes.
            assert len(self._bounds) == len(self._buckets)
            buckets = {
                f"le_{format(bound, '.17g')}": count
                for bound, count in zip(self._bounds, self._buckets)
            }
            buckets["inf"] = self._count
            return {
                "name": self.name,
                "count": self._count,
                "sum_ms": self._sum_ms,
                "buckets": buckets,
            }


class Stopwatch:
    """
        Simple time measuring class.
    """

    def __init__(self):
        self.timestamp = None
        self.time = None

    def start(self):
        """
            Start a time measurement
        """
        self.time = None
        self.timestamp = time.time()

    def lap(self):
        cur_time = time.time()
        start_time = self.timestamp
        self.timestamp = cur_time
        return cur_time - start_time

    @property
    def delta(self):
        if not self.timestamp:
            # stopped or not started
            return self.time or 0
        return time.time() - self.timestamp

    def stop(self):
        """
            Stop a running time measurement. returns the measured time
        """
        cur_time = time.time()
        start_time = self.timestamp or cur_time
        self.time = cur_time - start_time
        self.timestamp = None
        return self.time

    def __enter__(self):
        """
            Start stopwatch when entering with-block.
        """
        self.start()

    def __exit__(self, tpe, value, tb):
        """
            Stop stopwatch when exiting with-block.
        """
        self.stop()

    def __str__(self):
        cur_time = time.time()
        if self.timestamp:
            return str(self.time or cur_time - self.timestamp)
        else:
            return 'Not started'
