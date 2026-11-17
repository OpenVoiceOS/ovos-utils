"""Tests for the opt-in metrics exposition shared by OVOS services."""

import time
from urllib.request import urlopen

import pytest

from ovos_utils.metrics import (
    LatencyHistogram,
    metrics_recording_enabled,
    reset_metrics_recording_cache,
)
from ovos_utils.prometheus import (
    collect_histograms,
    load_metric_collectors,
    render_prometheus,
    start_metrics_server,
    stop_metrics_server,
)



@pytest.fixture(autouse=True)
def _recording_on(monkeypatch):
    """Recording is opt-in, so these tests opt in and clear the cache either side."""
    monkeypatch.setenv("OVOS_METRICS_ENABLED", "true")
    reset_metrics_recording_cache()
    yield
    monkeypatch.delenv("OVOS_METRICS_ENABLED", raising=False)
    reset_metrics_recording_cache()


class _EntryPoint:
    def __init__(self, name, value, collector):
        self.name, self.value, self._collector = name, value, collector

    def load(self):
        return self._collector


class _EntryPoints(list):
    def select(self, *, group):
        assert group == "ovos.performance.metrics"
        return self






def test_recording_is_off_until_the_endpoint_is_asked_for(monkeypatch):
    """The finding behind the gate: opt-in has to mean the recording too.

    ``metrics_enabled()`` was read by ``start_metrics_server()`` alone, so a
    default install still timed every stage and accumulated counters nobody
    could read.
    """
    monkeypatch.delenv("OVOS_METRICS_ENABLED", raising=False)
    reset_metrics_recording_cache()
    assert metrics_recording_enabled() is False

    histogram = LatencyHistogram("test_gate_ms", buckets_ms=(10, 50))
    histogram.observe_ms(5)
    with histogram.measure():
        pass
    assert histogram.snapshot()["count"] == 0, "a disabled histogram recorded"


def test_histogram_observes_exceptional_blocks():
    histogram = LatencyHistogram("test_stage_ms", buckets_ms=(10, 50))

    with pytest.raises(RuntimeError), histogram.measure():
        raise RuntimeError("expected")

    snapshot = histogram.snapshot()
    assert snapshot["count"] == 1
    assert snapshot["buckets"]["inf"] == 1


def test_histogram_measurement_can_exclude_nested_work(monkeypatch):
    clock = iter((10.0, 10.1))
    monkeypatch.setattr("ovos_utils.metrics.time.monotonic", lambda: next(clock))
    histogram = LatencyHistogram("test_stage_ms")

    with histogram.measure() as measurement:
        measurement.pause()

    snapshot = histogram.snapshot()
    assert snapshot["count"] == 1
    assert snapshot["sum_ms"] == pytest.approx(100.0)


def test_histogram_rejects_non_finite_observations():
    histogram = LatencyHistogram("test_stage_ms")

    with pytest.raises(ValueError, match="must be finite"):
        histogram.observe_ms(float("nan"))


def test_prometheus_renderer_converts_milliseconds_to_seconds():
    payload = render_prometheus({
        "test_stage_ms": {
            "count": 1,
            "sum_ms": 125.0,
            "buckets": {"le_100": 0, "le_250": 1, "inf": 1},
        },
    })

    assert 'test_stage_seconds_bucket{le="0.1"} 0' in payload
    assert 'test_stage_seconds_bucket{le="0.25"} 1' in payload
    assert "test_stage_seconds_sum 0.125" in payload
    assert "test_stage_seconds_count 1" in payload


def test_prometheus_renderer_supports_counters():
    payload = render_prometheus({
        "test_cache_hit_total": {"type": "counter", "value": 7},
    })

    assert "# TYPE test_cache_hit_total counter" in payload
    assert "test_cache_hit_total 7" in payload


def test_prometheus_renderer_rejects_malformed_counters():
    with pytest.raises(ValueError, match="must end with '_total'"):
        render_prometheus({
            "test_cache_hit": {"type": "counter", "value": 1},
        })


def test_collectors_reject_duplicate_metric_names():
    collector = lambda: {  # noqa: E731
        "duplicate_ms": {
            "count": 0,
            "sum_ms": 0,
            "buckets": {"inf": 0},
        },
    }

    with pytest.raises(ValueError, match="duplicate performance metric"):
        collect_histograms((("first", collector), ("second", collector)))


def test_renderer_rejects_exported_metric_name_collisions():
    snapshot = {
        "count": 0,
        "sum_ms": 0,
        "buckets": {"inf": 0},
    }

    with pytest.raises(ValueError, match="both export as"):
        render_prometheus({
            "duplicate_ms": snapshot,
            "duplicate_seconds": snapshot,
        })


def test_prometheus_renderer_preserves_sum_precision():
    payload = render_prometheus({
        "test_stage_ms": {
            "count": 1,
            "sum_ms": 1_000_000_000.125,
            "buckets": {"inf": 1},
        },
    })

    assert "test_stage_seconds_sum 1000000.000125" in payload


def test_plugin_metric_collectors_are_loaded_in_stable_order(monkeypatch):
    def plugin_collector():
        return {}

    class EntryPoint:
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def load(self):
            return plugin_collector

    class EntryPoints(list):
        def select(self, *, group):
            assert group == "ovos.performance.metrics"
            return self

    monkeypatch.setattr(
        "ovos_utils.prometheus.metadata.entry_points",
        lambda: EntryPoints((
            EntryPoint("weather", "weather:metrics"),
            EntryPoint("workshop", "workshop:metrics"),
        )),
    )

    collectors = load_metric_collectors()

    assert [name for name, _collector in collectors] == ["weather", "workshop"]


def test_a_collector_that_cannot_load_is_skipped_not_fatal(monkeypatch):
    """A half-installed plugin package raises ModuleNotFoundError on import.
    That used to propagate out of start_metrics_server and stop ovos-core
    before it connected to the bus; it must cost only that collector."""
    def healthy():
        return {}

    class Broken:
        name, value = "weather", "weather:metrics"

        def load(self):
            raise ModuleNotFoundError("No module named 'weather._metrics'")

    class NotCallable:
        name, value = "odd", "odd:metrics"

        def load(self):
            return 42

    class Healthy:
        name, value = "workshop", "workshop:metrics"

        def load(self):
            return healthy

    class EntryPoints(list):
        def select(self, *, group):
            return self

    monkeypatch.setattr(
        "ovos_utils.prometheus.metadata.entry_points",
        lambda: EntryPoints((Broken(), NotCallable(), Healthy())),
    )

    collectors = load_metric_collectors()

    assert [name for name, _collector in collectors] == ["workshop"]


@pytest.mark.parametrize("raw_port, why", [
    ("not-a-port", "unreadable"),
    ("70000", "out of range"),
    ("-1", "negative"),
])
def test_a_bad_port_disables_the_endpoint_and_nothing_else(monkeypatch, raw_port, why):
    """``__main__`` calls this before the ``try`` that guards startup.

    So a raise here did not merely skip the endpoint, it stopped the whole
    skills service: an unreadable ``OVOS_METRICS_PORT`` took the voice
    assistant down with it. The scrape endpoint is the least important thing
    in the process and must never be the reason it does not run.
    """
    monkeypatch.setenv("OVOS_METRICS_ENABLED", "true")
    monkeypatch.setenv("OVOS_METRICS_PORT", raw_port)

    server = start_metrics_server()

    assert server is None, f"a {why} port should leave the endpoint off"
    stop_metrics_server(server)


def test_a_port_already_taken_disables_the_endpoint_and_nothing_else(monkeypatch):
    """Same rule for a bind failure, which is the likelier one in production."""
    monkeypatch.setenv("OVOS_METRICS_ENABLED", "true")
    monkeypatch.setenv("OVOS_METRICS_PORT", "0")
    first = start_metrics_server()
    assert first is not None
    taken = first.server_address[1]
    try:
        monkeypatch.setenv("OVOS_METRICS_PORT", str(taken))
        second = start_metrics_server()
        assert second is None, "a taken port should leave the endpoint off"
        stop_metrics_server(second)
    finally:
        stop_metrics_server(first)



def test_the_endpoint_serves_a_callers_collectors_and_plugin_collectors(monkeypatch):
    """A service passes its own collectors; no second server implementation."""
    def audio_metrics():
        stage = LatencyHistogram("audio_playback_start_ms", buckets_ms=(10, 100))
        stage.observe_ms(20)
        return {"audio_playback_start_ms": stage.snapshot()}

    def fractional_counter():
        return {"test_fractional_work_total": {"type": "counter", "value": 1.6}}

    monkeypatch.setenv("OVOS_METRICS_ENABLED", "true")
    monkeypatch.setenv("OVOS_METRICS_HOST", "127.0.0.1")
    monkeypatch.setenv("OVOS_METRICS_PORT", "0")
    monkeypatch.setattr(
        "ovos_utils.prometheus.metadata.entry_points", lambda: _EntryPoints(
            (_EntryPoint("fractional", "x:y", fractional_counter),)))
    server = start_metrics_server([("audio", audio_metrics)])
    assert server is not None
    try:
        with urlopen(  # noqa: S310 - loopback test server only
            f"http://127.0.0.1:{server.server_address[1]}/metrics",
            timeout=2,
        ) as response:
            payload = response.read().decode()
        assert response.status == 200
        assert "audio_playback_start_seconds_count 1" in payload
        assert "test_fractional_work_total 1.6000000000000001" in payload
    finally:
        stop_metrics_server(server)


def test_the_endpoint_is_off_unless_metrics_are_enabled(monkeypatch):
    monkeypatch.delenv("OVOS_METRICS_ENABLED", raising=False)
    assert start_metrics_server([("x", lambda: {})]) is None


def test_other_paths_are_not_served(monkeypatch):
    monkeypatch.setenv("OVOS_METRICS_ENABLED", "true")
    monkeypatch.setenv("OVOS_METRICS_PORT", "0")
    monkeypatch.setattr("ovos_utils.prometheus.metadata.entry_points", lambda: _EntryPoints(()))
    server = start_metrics_server([])
    try:
        from urllib.error import HTTPError
        with pytest.raises(HTTPError) as error:
            urlopen(f"http://127.0.0.1:{server.server_address[1]}/other", timeout=2)  # noqa: S310
        assert error.value.code == 404
    finally:
        stop_metrics_server(server)


def test_a_histogram_can_use_its_own_enable_switch():
    stage = LatencyHistogram("own_switch_ms", buckets_ms=(1, 10), enabled=lambda: True)
    stage.observe_ms(2)
    assert stage.snapshot()["count"] == 1
