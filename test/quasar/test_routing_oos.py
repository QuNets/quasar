"""Tests for OOS routing baselines."""

from pathlib import Path

import pytest

from quasar.channel.models import EdgeAttributes, EdgeType
from quasar.routing import EntanglementRequest, OOSDSPRouter, OOSMPRRouter
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


def test_oos_dsp_selects_minimum_hop_path():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("gs-a", "gs-b", "sat-1", "sat-2", "sat-3"),
        edges=(
            LinkState(("gs-a", "sat-1"), EdgeType.SGL),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL),
            LinkState(("gs-a", "sat-2"), EdgeType.SGL),
            LinkState(("sat-2", "sat-3"), EdgeType.ISL),
            LinkState(("sat-3", "gs-b"), EdgeType.SGL),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = OOSDSPRouter().compute_route(snapshot, request, time=0.0)

    assert result.success
    assert result.path_tuple == ("gs-a", "sat-1", "gs-b")
    assert result.hop_count == 2
    assert result.success_probability is None
    assert result.fidelity is None


def test_oos_mpr_selects_higher_probability_path_with_more_hops():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("gs-a", "gs-b", "sat-low", "sat-1", "sat-2"),
        edges=(
            LinkState(("gs-a", "sat-low"), EdgeType.SGL),
            LinkState(("sat-low", "gs-b"), EdgeType.SGL),
            LinkState(("gs-a", "sat-1"), EdgeType.SGL),
            LinkState(("sat-1", "sat-2"), EdgeType.ISL),
            LinkState(("sat-2", "gs-b"), EdgeType.SGL),
        ),
    )
    edge_attributes = (
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("gs-a", "sat-low"),
            transmittance=0.2,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-low", "gs-b"),
            transmittance=0.2,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("gs-a", "sat-1"),
            transmittance=0.9,
        ),
        EdgeAttributes(
            edge_type=EdgeType.ISL,
            endpoints=("sat-1", "sat-2"),
            transmittance=0.9,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("sat-2", "gs-b"),
            transmittance=0.9,
        ),
    )
    request = EntanglementRequest(
        "gs-a",
        "gs-b",
        metadata={"edge_attributes": edge_attributes},
    )

    result = OOSMPRRouter().compute_route(snapshot, request, time=0.0)

    assert result.success
    assert result.path_tuple == ("gs-a", "sat-1", "sat-2", "gs-b")
    assert result.hop_count == 3
    assert result.success_probability == pytest.approx(0.9**3)
    assert result.fidelity is None
    assert result.storage_delay is None


def test_oos_mpr_falls_back_to_snapshot_transmittance():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("gs-a", "gs-b", "sat-1"),
        edges=(
            LinkState(("gs-a", "sat-1"), EdgeType.SGL, transmittance=0.5),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, transmittance=0.5),
        ),
    )
    request = EntanglementRequest("gs-a", "gs-b")

    result = OOSMPRRouter().compute_route(snapshot, request, time=0.0)

    assert result.success
    assert result.success_probability == 0.25


def test_oos_routers_do_not_import_sd_opportunity_selection():
    source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ("quasar/routing/dsp.py", "quasar/routing/mpr.py")
    )

    assert "SimultaneousDownlinkArchitecture" not in source
    assert "find_simultaneous_downlink_opportunities" not in source
    assert "SDRouter" not in source
