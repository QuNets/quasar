"""Tests for QUASAR-native event threshold detection."""

from pathlib import Path

from quasar.channel.models import EdgeType
from quasar.events import EventBridge, EventType, ThresholdCrossingDetector
from quasar.routing.base import RouteResult
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


def _snapshot(time, edges):
    return TopologySnapshot(
        time=time,
        nodes=("gs-a", "gs-b", "sat-1"),
        edges=edges,
    )


def _event_types(records):
    return [record.event_type for record in records]


def test_link_up_crossing_is_detected():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=False),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=True),),
    )

    records = EventBridge().detect_events(previous, current)

    assert EventType.LINK_UP in _event_types(records)
    assert EventType.GRAPH_UPDATE in _event_types(records)


def test_link_drop_crossing_is_detected():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=True),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=False),),
    )

    records = ThresholdCrossingDetector().detect(previous, current)

    assert EventType.LINK_DROP in _event_types(records)
    assert EventType.GRAPH_UPDATE in _event_types(records)


def test_fidelity_loss_crossing_is_detected_once():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, fidelity=0.80),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, fidelity=0.70),),
    )

    records = EventBridge().detect_events(
        previous,
        current,
        thresholds={"fidelity_threshold": 0.75},
    )

    assert EventType.FIDELITY_LOSS in _event_types(records)

    repeated = EventBridge().detect_events(
        current,
        _snapshot(0.2, (LinkState(("sat-1", "gs-a"), EdgeType.SGL, fidelity=0.65),)),
        thresholds={"fidelity_threshold": 0.75},
    )
    assert EventType.FIDELITY_LOSS not in _event_types(repeated)


def test_fidelity_recovery_crossing_is_detected():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, fidelity=0.70),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, fidelity=0.80),),
    )

    records = EventBridge().detect_events(
        previous,
        current,
        thresholds={"fidelity_threshold": 0.75},
    )

    assert EventType.FIDELITY_RECOVERY in _event_types(records)


def test_channel_degradation_crossing_is_detected():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.60),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.30),),
    )

    records = EventBridge().detect_events(
        previous,
        current,
        thresholds={"channel_quality_threshold": 0.50},
    )

    assert EventType.CHANNEL_DEGRADATION in _event_types(records)


def test_channel_recovery_crossing_is_detected():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.30),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.60),),
    )

    records = EventBridge().detect_events(
        previous,
        current,
        thresholds={"channel_quality_threshold": 0.50},
    )

    assert EventType.CHANNEL_RECOVERY in _event_types(records)


def test_graph_update_is_detected_when_available_edge_set_changes():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=True),),
    )
    current = _snapshot(
        0.1,
        (
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=True),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, available=True),
        ),
    )

    records = EventBridge().detect_events(previous, current)

    assert EventType.GRAPH_UPDATE in _event_types(records)


def test_route_recompute_record_is_generated_for_failed_route_edge():
    previous = _snapshot(
        0.0,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=True),),
    )
    current = _snapshot(
        0.1,
        (LinkState(("sat-1", "gs-a"), EdgeType.SGL, available=False),),
    )
    route = RouteResult(path=("gs-a", "sat-1"), success=True)

    records = EventBridge().detect_events(previous, current, current_route=route)

    assert EventType.ROUTE_RECOMPUTE in _event_types(records)
    recompute = [
        record
        for record in records
        if record.event_type == EventType.ROUTE_RECOMPUTE
    ][0]
    assert recompute.reason == "current route uses a failed edge"


def test_events_module_has_no_run_loop_routing_or_simqn_binding():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/events").glob("*.py")
    )

    assert "def run(" not in source
    assert "compute_route" not in source
    assert "SDRouter" not in source
    assert "OOSDSPRouter" not in source
    assert "OOSMPRRouter" not in source
    assert "OOSEASRRouter" not in source
    assert "from qns" not in source
    assert "import qns" not in source
