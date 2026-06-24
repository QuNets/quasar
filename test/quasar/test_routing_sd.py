"""Tests for SD-specific routing selection."""

from pathlib import Path

from quasar.channel.models import EdgeType
from quasar.routing import EntanglementRequest, SDRouter
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


def test_sd_router_selects_only_feasible_dual_downlink_opportunities():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "sat-2", "sat-3", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.9),
            LinkState(("sat-2", "gs-b"), EdgeType.SGL, transmittance=0.9),
            LinkState(("sat-3", "gs-a"), EdgeType.SGL, transmittance=0.3),
            LinkState(("sat-3", "gs-b"), EdgeType.SGL, transmittance=0.4),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = SDRouter().compute_route(snapshot, request, time=0.0)

    assert result.success
    selected = result.metadata["selected_opportunity"]
    assert selected.metadata["satellite"] == "sat-3"


def test_sd_router_chooses_highest_joint_transmittance():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "sat-2", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.9),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, transmittance=0.2),
            LinkState(("sat-2", "gs-a"), EdgeType.SGL, transmittance=0.5),
            LinkState(("sat-2", "gs-b"), EdgeType.SGL, transmittance=0.5),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = SDRouter().compute_route(snapshot, request, time=0.0)

    assert result.success_probability == 0.25
    selected = result.metadata["selected_opportunity"]
    assert selected.metadata["satellite"] == "sat-2"
    assert result.metadata["score"] == 0.25


def test_sd_router_returns_infeasible_without_common_satellite():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "sat-2", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.9),
            LinkState(("sat-2", "gs-b"), EdgeType.SGL, transmittance=0.9),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = SDRouter().compute_route(snapshot, request, time=0.0)

    assert not result.success
    assert result.reason == "no simultaneous downlink opportunity"
    assert result.metadata["opportunities"] == ()


def test_sd_router_storage_delay_is_zero():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.4),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, transmittance=0.5),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = SDRouter().compute_route(snapshot, request, time=0.0)

    assert result.storage_delay == 0.0


def test_sd_router_does_not_import_memory_or_oos_architecture():
    source = Path("quasar/routing/sd.py").read_text(encoding="utf-8")

    assert "quasar.memory" not in source
    assert "fidelity_after_storage" not in source
    assert "OnOrbitStitchingArchitecture" not in source
