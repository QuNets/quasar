"""Tests for the minimal QUASAR topology engine."""

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.topology.engine import SpatiotemporalTopologyEngine
from quasar.topology.visibility import apply_visibility_mask


def test_low_elevation_link_is_pruned():
    link = LinkState(
        endpoints=("sat-1", "gs-1"),
        edge_type=EdgeType.SGL,
        distance_km=500.0,
        elevation_deg=5.0,
    )

    masked = apply_visibility_mask(link, min_elevation_deg=15.0)

    assert not masked.available


def test_out_of_range_link_is_pruned():
    link = LinkState(
        endpoints=("sat-1", "sat-2"),
        edge_type=EdgeType.ISL,
        distance_km=2500.0,
    )

    masked = apply_visibility_mask(link, max_range_km=1000.0)

    assert not masked.available


def test_build_snapshot_counts_available_edges():
    engine = SpatiotemporalTopologyEngine(
        satellites=[Satellite("sat-1"), Satellite("sat-2")],
        ground_stations=[GroundStation("gs-1", latitude_deg=30.0, longitude_deg=120.0)],
        min_elevation_deg=15.0,
        max_sgl_range_km=1000.0,
        max_isl_range_km=1500.0,
    )
    candidate_links = [
        LinkState(
            endpoints=("sat-1", "gs-1"),
            edge_type=EdgeType.SGL,
            distance_km=600.0,
            elevation_deg=30.0,
        ),
        LinkState(
            endpoints=("sat-2", "gs-1"),
            edge_type=EdgeType.SGL,
            distance_km=600.0,
            elevation_deg=8.0,
        ),
        LinkState(
            endpoints=("sat-1", "sat-2"),
            edge_type=EdgeType.ISL,
            distance_km=2000.0,
        ),
    ]

    snapshot = engine.build_snapshot(time=1.0, candidate_links=candidate_links)

    assert snapshot.node_count == 3
    assert len(snapshot.edges) == 3
    assert snapshot.edge_count == 1
    assert len(snapshot.available_edges) == 1
    assert snapshot.available_edges[0].endpoints == ("sat-1", "gs-1")
