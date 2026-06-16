"""Tests for QUASAR metrics logs and traces."""

from pathlib import Path

import pytest

from quasar.channel.models import EdgeAttributes, EdgeType
from quasar.events import EventRecord, EventType
from quasar.metrics import (
    EdgeTrace,
    EventLog,
    MetricSample,
    MetricSummary,
    PathTrace,
)
from quasar.routing.base import RouteResult


def test_event_log_records_multiple_events_and_counts_by_type():
    event_log = EventLog()
    events = (
        EventRecord(EventType.LINK_DROP, time=0.1),
        EventRecord(EventType.FIDELITY_LOSS, time=0.2),
        EventRecord(EventType.GRAPH_UPDATE, time=0.3),
        EventRecord(EventType.ROUTE_RECOMPUTE, time=0.4),
        EventRecord(EventType.LINK_DROP, time=0.5),
    )

    event_log.extend(events)

    counts = event_log.count_by_type()
    assert event_log.total_count == 5
    assert counts[EventType.LINK_DROP] == 2
    assert counts[EventType.FIDELITY_LOSS] == 1
    assert counts[EventType.GRAPH_UPDATE] == 1
    assert counts[EventType.ROUTE_RECOMPUTE] == 1
    assert event_log.to_records() == events


def test_edge_trace_records_edge_attributes():
    trace = EdgeTrace()
    attributes = EdgeAttributes(
        edge_type=EdgeType.SGL,
        endpoints=("sat-1", "gs-a"),
        available=True,
        transmittance=0.4,
        success_probability=0.3,
        fidelity=0.9,
        storage_delay=0.01,
    )

    record = trace.record(time=0.1, edge=("sat-1", "gs-a"), attributes=attributes)

    assert record.endpoints == ("sat-1", "gs-a")
    assert record.edge_type == EdgeType.SGL
    assert record.transmittance == 0.4
    assert record.success_probability == 0.3
    assert record.fidelity == 0.9
    assert record.storage_delay == 0.01


def test_edge_trace_computes_edge_averages_and_availability_ratio():
    trace = EdgeTrace()
    trace.record(
        time=0.1,
        edge=("sat-1", "gs-a"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-1", "gs-a"),
            transmittance=0.4,
            success_probability=0.3,
            fidelity=0.9,
        ),
    )
    trace.record(
        time=0.2,
        edge=("sat-2", "gs-b"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-2", "gs-b"),
            available=False,
            transmittance=0.2,
            success_probability=0.1,
            fidelity=0.7,
        ),
    )

    assert trace.available_edge_ratio() == 0.5
    assert trace.average_transmittance() == pytest.approx(0.3)
    assert trace.average_success_probability() == pytest.approx(0.2)
    assert trace.average_fidelity() == pytest.approx(0.8)


def test_path_trace_records_successful_and_failed_routes():
    trace = PathTrace()
    success = RouteResult(
        path=("gs-a", "sat-1", "gs-b"),
        success=True,
        cost=1.0,
        success_probability=0.5,
        fidelity=0.9,
        storage_delay=0.01,
    )
    failure = RouteResult(success=False, reason="no path")

    trace.record(time=0.1, route_result=success, algorithm="oos_easr")
    trace.record(time=0.2, route_result=failure, algorithm="oos_easr")

    records = trace.records
    assert records[0].path == ("gs-a", "sat-1", "gs-b")
    assert records[0].success
    assert not records[1].success
    assert trace.success_rate() == 0.5


def test_metric_summary_from_logs_combines_event_edge_and_path_metrics():
    event_log = EventLog()
    event_log.record(EventRecord(EventType.LINK_DROP, time=0.1))
    event_log.record(EventRecord(EventType.ROUTE_RECOMPUTE, time=0.2))

    edge_trace = EdgeTrace()
    edge_trace.record(
        time=0.1,
        edge=("sat-1", "gs-a"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-1", "gs-a"),
            transmittance=0.4,
            success_probability=0.3,
            fidelity=0.8,
        ),
    )

    path_trace = PathTrace()
    path_trace.record(time=0.1, route_result=RouteResult(success=True, cost=2.0))
    path_trace.record(time=0.2, route_result=RouteResult(success=False))

    summary = MetricSummary.from_logs(event_log, edge_trace, path_trace)
    data = summary.to_dict()

    assert data["total_events"] == 2
    assert data["event_counts"]["LINK_DROP"] == 1
    assert data["event_counts"]["ROUTE_RECOMPUTE"] == 1
    assert data["available_edge_ratio"] == 1.0
    assert data["average_transmittance"] == 0.4
    assert data["average_success_probability"] == 0.3
    assert data["average_fidelity"] == 0.8
    assert data["routing_success_rate"] == 0.5
    assert data["path_count"] == 2
    assert data["edge_record_count"] == 1


def test_metric_sample_holds_point_in_time_values():
    sample = MetricSample(
        time=1.0,
        available_edge_ratio=0.5,
        average_transmittance=0.4,
        average_success_probability=0.3,
        average_fidelity=0.8,
        routing_success_rate=0.25,
        event_count=3,
    )

    assert sample.time == 1.0
    assert sample.event_count == 3


def test_metrics_module_has_no_routing_detection_run_loop_or_simqn_scheduler():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/metrics").glob("*.py")
    )

    assert "SDRouter" not in source
    assert "OOSDSPRouter" not in source
    assert "OOSMPRRouter" not in source
    assert "OOSEASRRouter" not in source
    assert "compute_route" not in source
    assert "EventBridge" not in source
    assert "detect_events" not in source
    assert "func_to_event" not in source
    assert "Simulator" not in source
    assert "add_event" not in source
    assert "def run(" not in source
    assert "100 ms" not in source
    assert "route recomputation" not in source
