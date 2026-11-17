"""Dependency-free Prometheus exposition for one OVOS process.

Any OVOS service (core, audio, the listener) can expose its performance
metrics with one call and without a second implementation::

    from ovos_utils.prometheus import start_metrics_server, stop_metrics_server

    server = start_metrics_server([("audio", my_histograms)])
    ...
    stop_metrics_server(server)

Nothing is enabled by default. The scrape endpoint and the recording done by
:class:`ovos_utils.metrics.LatencyHistogram` are switched on together by
``OVOS_METRICS_ENABLED``; ``OVOS_METRICS_HOST`` (default ``127.0.0.1``) and
``OVOS_METRICS_PORT`` (default ``9474``) choose where the endpoint listens.

A *collector* is a zero-argument callable returning a mapping of metric name to
snapshot (see :meth:`ovos_utils.metrics.LatencyHistogram.snapshot`; a counter
is ``{"type": "counter", "value": n}``). Plugins add theirs to the
``ovos.performance.metrics`` entry-point group and are discovered when the
server starts; a plugin collector that cannot be imported, or is not callable,
is logged and skipped, because a metrics extra must never stop the service it
observes.
"""

import math
import re
from collections.abc import Callable, Mapping, Sequence
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import metadata
import os
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple

from ovos_utils.log import LOG
from ovos_utils.metrics import metrics_enabled

METRIC_ENTRYPOINT_GROUP = "ovos.performance.metrics"
_PROMETHEUS_NAME = re.compile(r"[a-zA-Z_:][a-zA-Z0-9_:]*")
MetricCollector = Callable[[], Mapping[str, Mapping[str, object]]]


def load_metric_collectors(
    extra: Optional[Sequence[Tuple[str, MetricCollector]]] = None,
) -> Tuple[Tuple[str, MetricCollector], ...]:
    """Collectors passed in ``extra`` plus those installed plugins register.

    Plugin collectors are ordered by entry-point name and value so the output
    is stable. One that cannot be loaded, or is not callable, costs only its
    own metrics.
    """
    collectors: List[Tuple[str, MetricCollector]] = list(extra or ())
    discovered = metadata.entry_points()
    if hasattr(discovered, "select"):
        entry_points = discovered.select(group=METRIC_ENTRYPOINT_GROUP)
    else:  # pragma: no cover - Python 3.9 compatibility path
        entry_points = discovered.get(METRIC_ENTRYPOINT_GROUP, ())
    entry_points = sorted(
        entry_points,
        key=lambda entry_point: (entry_point.name, entry_point.value),
    )
    for entry_point in entry_points:
        # A collector is an optional extra shipped by a plugin. A half-installed
        # package or a missing dependency raises on import, and this runs
        # before the service connects to anything, so raising here would stop
        # the service from starting.
        try:
            collector = entry_point.load()
        except Exception as error:
            LOG.error(
                "metrics collector %r could not be loaded (%s: %s); "
                "it is skipped", entry_point.name, type(error).__name__, error)
            continue
        if not callable(collector):
            LOG.error(
                "metrics entry point %r is not callable; it is skipped",
                entry_point.name)
            continue
        collectors.append((entry_point.name, collector))
    return tuple(collectors)


def collect_histograms(
    collectors: Sequence[Tuple[str, MetricCollector]],
) -> Dict[str, Mapping[str, object]]:
    """Collect a snapshot and reject duplicate or malformed metric names."""
    histograms: Dict[str, Mapping[str, object]] = {}
    for collector_name, collector in collectors:
        snapshots = collector()
        if not isinstance(snapshots, Mapping):
            raise TypeError(
                f"metrics collector {collector_name!r} returned a non-mapping"
            )
        for metric_name, snapshot in snapshots.items():
            if metric_name in histograms:
                raise ValueError(f"duplicate performance metric {metric_name!r}")
            if not isinstance(snapshot, Mapping):
                raise TypeError(
                    f"performance metric {metric_name!r} is not a mapping"
                )
            histograms[str(metric_name)] = snapshot
    return histograms


def _number(value: Any, field: str, metric_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{metric_name}.{field} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{metric_name}.{field} must be finite and non-negative")
    return parsed


def _count(value: Any, field: str, metric_name: str) -> int:
    parsed = _number(value, field, metric_name)
    if not parsed.is_integer():
        raise ValueError(f"{metric_name}.{field} must be an integer")
    return int(parsed)


def _metric_name(metric_name: str) -> str:
    exported = (
        f"{metric_name[:-3]}_seconds"
        if metric_name.endswith("_ms")
        else metric_name
    )
    if not _PROMETHEUS_NAME.fullmatch(exported):
        raise ValueError(f"invalid Prometheus metric name {exported!r}")
    return exported


def render_prometheus(
    metrics: Mapping[str, Mapping[str, object]],
) -> str:
    """Render process-local histogram and counter snapshots."""
    lines: List[str] = []
    exported_names: Dict[str, str] = {}
    for metric_name in sorted(metrics):
        snapshot = metrics[metric_name]
        exported = _metric_name(metric_name)
        previous = exported_names.setdefault(exported, metric_name)
        if previous != metric_name:
            raise ValueError(
                f"metrics {previous!r} and {metric_name!r} both export as "
                f"{exported!r}"
            )
        metric_type = snapshot.get("type", "histogram")
        if metric_type == "counter":
            if not exported.endswith("_total"):
                raise ValueError(
                    f"counter metric {metric_name!r} must end with '_total'"
                )
            value = _number(snapshot.get("value"), "value", metric_name)
            lines.extend((
                f"# HELP {exported} Cumulative {metric_name}.",
                f"# TYPE {exported} counter",
                f"{exported} {value:.17g}",
            ))
            continue
        if metric_type != "histogram":
            raise ValueError(
                f"unsupported performance metric type {metric_type!r}"
            )
        buckets = snapshot.get("buckets")
        if not isinstance(buckets, Mapping):
            raise TypeError(f"{metric_name}.buckets must be a mapping")
        count = _count(snapshot.get("count"), "count", metric_name)
        sum_seconds = _number(
            snapshot.get("sum_ms"), "sum_ms", metric_name
        ) / 1_000
        finite: List[Tuple[float, int]] = []
        infinity_count: Optional[int] = None
        for bucket_name, raw_count in buckets.items():
            bucket_count = _count(raw_count, str(bucket_name), metric_name)
            if bucket_name == "inf":
                infinity_count = bucket_count
                continue
            if not str(bucket_name).startswith("le_"):
                raise ValueError(
                    f"unexpected bucket {bucket_name!r} in {metric_name}"
                )
            bound_ms = float(str(bucket_name)[3:])
            if not math.isfinite(bound_ms) or bound_ms < 0:
                raise ValueError(f"invalid bucket bound in {metric_name}")
            finite.append((bound_ms, bucket_count))
        finite.sort(key=lambda item: item[0])
        cumulative = [bucket_count for _, bucket_count in finite]
        if cumulative != sorted(cumulative):
            raise ValueError(f"non-cumulative buckets in {metric_name}")
        if cumulative and cumulative[-1] > count:
            raise ValueError(f"bucket exceeds count in {metric_name}")
        if infinity_count != count:
            raise ValueError(
                f"{metric_name} infinity bucket does not equal count"
            )
        lines.extend((
            f"# HELP {exported} Latency observed by {metric_name}.",
            f"# TYPE {exported} histogram",
        ))
        for bound_ms, bucket_count in finite:
            lines.append(
                f'{exported}_bucket{{le="{bound_ms / 1_000:g}"}} '
                f"{bucket_count}"
            )
        lines.extend((
            f'{exported}_bucket{{le="+Inf"}} {count}',
            f"{exported}_sum {sum_seconds:.17g}",
            f"{exported}_count {count}",
        ))
    return "\n".join(lines) + "\n"


def _handler(
    collectors: Sequence[Tuple[str, MetricCollector]],
) -> type:
    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/metrics":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                payload = render_prometheus(collect_histograms(collectors))
            except Exception:
                LOG.exception("OVOS metrics scrape failed")
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            encoded = payload.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type",
                "text/plain; version=0.0.4; charset=utf-8",
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, _format: str, *args: object) -> None:
            return

    return MetricsHandler


def start_metrics_server(
    collectors: Optional[Sequence[Tuple[str, MetricCollector]]] = None,
) -> Optional[ThreadingHTTPServer]:
    """Start a daemon metrics listener when metrics are enabled.

    Args:
        collectors: ``(name, collector)`` pairs to expose in addition to the
            ones installed plugins register; the caller's own metrics.

    Returns the server so the caller can pass it to
    :func:`stop_metrics_server`, or ``None`` when metrics are off or the
    listener could not start.

    Never raises. Services call this during startup, so a raise here would let
    an opt-in scrape endpoint -- an unreadable ``OVOS_METRICS_PORT``, a port
    already in use -- stop the process it only observes. The misconfiguration
    is logged and the endpoint stays off.
    """
    if not metrics_enabled():
        return None
    host = os.getenv("OVOS_METRICS_HOST", "127.0.0.1")
    raw_port = os.getenv("OVOS_METRICS_PORT", "9474")
    try:
        port = int(raw_port)
    except ValueError:
        LOG.error(
            "OVOS_METRICS_PORT must be an integer, got %r; "
            "the metrics listener is disabled", raw_port)
        return None
    if not 0 <= port <= 65_535:
        LOG.error(
            "OVOS_METRICS_PORT must be between 0 and 65535, got %s; "
            "the metrics listener is disabled", port)
        return None
    try:
        all_collectors = load_metric_collectors(collectors)
        server = ThreadingHTTPServer((host, port), _handler(all_collectors))
    except OSError as error:
        # Address in use, permission denied on a privileged port, bad host.
        LOG.error(
            "the metrics listener could not bind %s:%s (%s); it is disabled",
            host, port, error)
        return None
    Thread(
        target=server.serve_forever,
        name="ovos-metrics",
        daemon=True,
    ).start()
    LOG.info(
        "OVOS metrics listener started on %s:%s",
        host,
        server.server_address[1],
    )
    return server


def stop_metrics_server(server: Optional[ThreadingHTTPServer]) -> None:
    """Stop and close a metrics listener, if one was started."""
    if server is None:
        return
    server.shutdown()
    server.server_close()
