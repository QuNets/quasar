"""Tests for OOS EASR routing."""

from math import log
from pathlib import Path

import pytest

from quasar.channel.models import EdgeAttributes, EdgeType
from quasar.routing import EntanglementRequest, OOSEASRRouter
from quasar.routing.easr import easr_edge_weight
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


def _snapshot() -> TopologySnapshot:
    return TopologySnapshot(
        time=0.0,
        nodes=("gs-a", "gs-b", "sat-high", "sat-low"),
        edges=(
            LinkState(("gs-a", "sat-high"), EdgeType.SGL),
            LinkState(("sat-high", "gs-b"), EdgeType.SGL),
            LinkState(("gs-a", "sat-low"), EdgeType.SGL),
            LinkState(("sat-low", "gs-b"), EdgeType.SGL),
        ),
    )


def _edge_attributes(high_delay: float = 0.2):
    return (
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("gs-a", "sat-high"),
            transmittance=0.9,
            storage_delay=high_delay,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-high", "gs-b"),
            transmittance=0.9,
            storage_delay=0.0,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("gs-a", "sat-low"),
            transmittance=0.7,
            storage_delay=0.0,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-low", "gs-b"),
            transmittance=0.7,
            storage_delay=0.0,
        ),
    )


def test_easr_edge_weight_matches_formula():
    edge = EdgeAttributes(
        edge_type=EdgeType.ISL,
        endpoints=("sat-a", "sat-b"),
        transmittance=0.8,
    )

    weight = easr_edge_weight(
        edge=edge,
        tau_c=0.5,
        xi=2.0,
        swap_success_probability=0.5,
        storage_delay=0.25,
    )

    assert weight == pytest.approx(-log(0.8) - log(0.5) + 2.0 * 0.25 / 0.5)


def test_easr_selects_higher_combined_score_oos_path():
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": _edge_attributes()},
    )
    router = OOSEASRRouter(tau_c=0.1, xi=1.0, fidelity_threshold=0.0)

    result = router.compute_route(_snapshot(), request, time=0.0)

    assert result.success
    assert result.path_tuple == ("gs-a", "sat-low", "gs-b")
    assert result.metadata["objective_score"] == pytest.approx(0.7 * 0.7)


def test_easr_penalizes_storage_delay():
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": _edge_attributes(high_delay=0.3)},
    )
    router = OOSEASRRouter(tau_c=0.1, xi=1.0, fidelity_threshold=0.0)

    result = router.compute_route(_snapshot(), request, time=0.0)

    assert result.success
    assert result.path_tuple == ("gs-a", "sat-low", "gs-b")
    assert result.storage_delay == 0.0


def test_easr_route_is_infeasible_below_fidelity_threshold():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("gs-a", "gs-b", "sat-1"),
        edges=(
            LinkState(("gs-a", "sat-1"), EdgeType.SGL),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL),
        ),
    )
    edge_attributes = (
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("gs-a", "sat-1"),
            transmittance=0.9,
            storage_delay=0.08,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-1", "gs-b"),
            transmittance=0.9,
            storage_delay=0.08,
        ),
    )
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": edge_attributes},
    )
    router = OOSEASRRouter(tau_c=0.1, xi=0.0, fidelity_threshold=0.5)

    result = router.compute_route(snapshot, request, time=0.0)

    assert not result.success
    assert result.reason == "fidelity below threshold"
    assert result.path_tuple == ("gs-a", "sat-1", "gs-b")


def test_easr_tau_c_changes_temporal_penalty():
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": _edge_attributes(high_delay=0.2)},
    )

    short_memory = OOSEASRRouter(tau_c=0.05, xi=1.0, fidelity_threshold=0.0)
    long_memory = OOSEASRRouter(tau_c=10.0, xi=1.0, fidelity_threshold=0.0)

    short_result = short_memory.compute_route(_snapshot(), request, time=0.0)
    long_result = long_memory.compute_route(_snapshot(), request, time=0.0)

    assert short_result.path_tuple == ("gs-a", "sat-low", "gs-b")
    assert long_result.path_tuple == ("gs-a", "sat-high", "gs-b")


def test_easr_with_xi_zero_is_close_to_success_probability_selection():
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": _edge_attributes(high_delay=10.0)},
    )
    router = OOSEASRRouter(tau_c=0.1, xi=0.0, fidelity_threshold=0.0)

    result = router.compute_route(_snapshot(), request, time=0.0)

    assert result.success
    assert result.path_tuple == ("gs-a", "sat-high", "gs-b")
    assert result.success_probability == pytest.approx(0.9 * 0.9)


def test_easr_does_not_import_or_call_sd_router():
    source = Path("quasar/routing/easr.py").read_text(encoding="utf-8")

    assert "SDRouter" not in source
    assert "SDOpportunitySelector" not in source
    assert "SimultaneousDownlinkArchitecture" not in source


def test_easr_does_not_implement_events_or_polling():
    source = Path("quasar/routing/easr.py").read_text(encoding="utf-8")

    assert "EventBridge" not in source
    assert "GRAPH_UPDATE" not in source
    assert "ROUTE_RECOMPUTE" not in source
    assert "def run(" not in source
    assert "100 ms" not in source
