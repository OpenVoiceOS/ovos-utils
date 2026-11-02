# Performance metrics

**Modules:** `ovos_utils.metrics`, `ovos_utils.prometheus`

Latency histograms, a Prometheus text renderer, an opt-in scrape endpoint and
plugin collector discovery, with no dependencies beyond the standard library.
Any OVOS process (core, audio, the listener) can use them; none needs its own
metrics server or its own copy of the histogram.

Metrics are off by default. `OVOS_METRICS_ENABLED=true` switches on both the
recording done by `LatencyHistogram` and the scrape endpoint, so a process that
never asked for metrics does not accumulate counters nobody can read.
`OVOS_METRICS_HOST` (default `127.0.0.1`) and `OVOS_METRICS_PORT` (default
`9474`) choose where the endpoint listens.

---

## `LatencyHistogram`

```python
from ovos_utils.metrics import LatencyHistogram

STAGE = LatencyHistogram("ovos_audio_playback_start_ms")

with STAGE.measure() as measurement:   # records on exit, even on an exception
    ...
    measurement.pause()                # exclude nested work from the timing
    ...
    measurement.resume()

@STAGE.timed
def handler(): ...
```

`observe_ms(value)` records one finite, non-negative duration, and does nothing
while recording is off. `snapshot()` returns a detached mapping with `name`,
`count`, `sum_ms` and cumulative `buckets` (`le_<bound>` and `inf`). Pass
`enabled=callable` to decide recording yourself instead of `OVOS_METRICS_ENABLED`.
`metrics_enabled()`, `metrics_recording_enabled()` (cached) and
`reset_metrics_recording_cache()` (for tests) expose the switch.

## Exposing metrics

```python
from ovos_utils.prometheus import start_metrics_server, stop_metrics_server

server = start_metrics_server([("audio", lambda: {STAGE.name: STAGE.snapshot()})])
...
stop_metrics_server(server)
```

`start_metrics_server(collectors)` returns the server, or `None` when metrics
are off or the listener could not start. It never raises: a bad
`OVOS_METRICS_PORT` or a port already in use is logged and the endpoint stays
off, because a scrape endpoint must not stop the process it observes.

A *collector* is a callable returning `{metric_name: snapshot}`. A snapshot is a
histogram snapshot, or `{"type": "counter", "value": n}` (the name must end in
`_total`). A name ending `_ms` is exported as `_seconds`.

## Plugin collectors

A plugin adds its collector to the `ovos.performance.metrics` entry-point group;
`load_metric_collectors()` finds it when the server starts. A collector that
cannot be imported, or is not callable, is logged and skipped: a metrics extra
costs only its own metrics, never the service.
