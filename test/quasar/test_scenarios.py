"""Tests for QUASAR scenario data sources."""

from pathlib import Path

import pytest

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.scenarios import (
    ScenarioFrame,
    TLESGP4Source,
    TraceReplaySource,
    WalkerDeltaConfig,
    WalkerDeltaLiteSource,
)
from quasar.topology.engine import SpatiotemporalTopologyEngine


TLE_FIXTURE = Path("examples/data/tle_sample.tle")


def _ground_station() -> GroundStation:
    return GroundStation("GS-A", latitude_deg=0.0, longitude_deg=0.0)


def test_walker_delta_config_defaults_match_baseline_direction():
    config = WalkerDeltaConfig(
        planes=2,
        satellites_per_plane=3,
        ground_stations=(_ground_station(),),
    )

    assert config.altitude_km == 500.0
    assert config.inclination_deg == 53.0
    assert config.dt == 0.1
    assert config.min_elevation_deg == 15.0


def test_walker_delta_lite_frame_returns_scenario_frame():
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=2,
            satellites_per_plane=2,
            ground_stations=(_ground_station(),),
        )
    )

    frame = source.frame_at(0.0)

    assert isinstance(frame, ScenarioFrame)
    assert frame.time == 0.0
    assert len(frame.satellites) == 4
    assert len(frame.ground_stations) == 1
    assert frame.metadata["source"] == "walker_delta_lite"
    assert "satellite_positions" in frame.metadata


def test_walker_delta_lite_candidate_links_are_link_states():
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=2,
            satellites_per_plane=2,
            ground_stations=(_ground_station(),),
        )
    )

    links = source.candidate_links_at(0.0)

    assert isinstance(links, tuple)
    assert links
    assert all(isinstance(link, LinkState) for link in links)


def test_walker_delta_lite_generates_sgl_candidate_links():
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=1,
            satellites_per_plane=2,
            ground_stations=(_ground_station(),),
            include_isl=False,
        )
    )

    links = source.candidate_links_at(0.0)
    sgl_links = [link for link in links if link.edge_type == EdgeType.SGL]

    assert sgl_links
    assert all(link.distance_km is not None for link in sgl_links)
    assert all(link.elevation_deg is not None for link in sgl_links)


def test_walker_delta_lite_generates_isl_candidate_links():
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=2,
            satellites_per_plane=2,
            ground_stations=(_ground_station(),),
            include_sgl=False,
        )
    )

    links = source.candidate_links_at(0.0)
    isl_links = [link for link in links if link.edge_type == EdgeType.ISL]

    assert isl_links
    assert all(link.distance_km is not None for link in isl_links)
    assert all(link.elevation_deg is None for link in isl_links)


def test_walker_candidate_links_feed_existing_topology_engine():
    ground_station = _ground_station()
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=2,
            satellites_per_plane=2,
            ground_stations=(ground_station,),
        )
    )
    frame = source.frame_at(0.0)
    engine = SpatiotemporalTopologyEngine(
        satellites=frame.satellites,
        ground_stations=frame.ground_stations,
        min_elevation_deg=0.0,
        max_sgl_range_km=None,
        max_isl_range_km=None,
    )

    snapshot = engine.build_snapshot(
        time=frame.time,
        candidate_links=frame.candidate_links,
    )

    assert snapshot.node_count == len(frame.satellites) + len(frame.ground_stations)
    assert len(snapshot.edges) == len(frame.candidate_links)


def test_trace_replay_source_returns_user_provided_frame():
    satellite = Satellite("SAT-1")
    station = _ground_station()
    link = LinkState(("SAT-1", "GS-A"), EdgeType.SGL, distance_km=500.0, elevation_deg=30.0)
    frame = ScenarioFrame(
        time=0.0,
        satellites=(satellite,),
        ground_stations=(station,),
        candidate_links=(link,),
    )
    source = TraceReplaySource(frames={0.0: frame})

    replayed = source.frame_at(0.0)

    assert replayed is frame
    assert source.candidate_links_at(0.0) == (link,)


def test_trace_replay_source_supports_previous_frame_mode():
    satellite = Satellite("SAT-1")
    station = _ground_station()
    link = LinkState(("SAT-1", "GS-A"), EdgeType.SGL, distance_km=500.0, elevation_deg=30.0)
    source = TraceReplaySource(
        candidate_links_by_time={0.0: (link,)},
        satellites=(satellite,),
        ground_stations=(station,),
        mode="previous",
    )

    frame = source.frame_at(0.5)

    assert frame.time == 0.0
    assert frame.candidate_links == (link,)


def test_tle_sgp4_source_reads_tle_file_and_returns_frame():
    pytest.importorskip("sgp4.api")
    station = _ground_station()
    source = TLESGP4Source.from_file(
        TLE_FIXTURE,
        ground_stations=(station,),
        include_isl=False,
    )

    frame = source.frame_at(0.0)

    assert isinstance(frame, ScenarioFrame)
    assert frame.metadata["source"] == "tle_sgp4"
    assert len(frame.satellites) == 2
    assert frame.ground_stations == (station,)
    assert "satellite_positions" in frame.metadata
    assert "satellite_subpoints" in frame.metadata


def test_tle_sgp4_source_generates_sgl_candidate_links():
    pytest.importorskip("sgp4.api")
    source = TLESGP4Source.from_file(
        TLE_FIXTURE,
        ground_stations=(_ground_station(),),
        include_isl=False,
    )

    links = source.candidate_links_at(60.0)
    sgl_links = [link for link in links if link.edge_type == EdgeType.SGL]

    assert len(sgl_links) == 2
    assert all(link.distance_km is not None for link in sgl_links)
    assert all(link.elevation_deg is not None for link in sgl_links)
    assert all(link.metadata["source"] == "tle_sgp4" for link in sgl_links)


def test_tle_sgp4_source_generates_optional_isl_candidate_links():
    pytest.importorskip("sgp4.api")
    source = TLESGP4Source.from_file(
        TLE_FIXTURE,
        ground_stations=(_ground_station(),),
        include_isl=True,
    )

    links = source.candidate_links_at(0.0)
    isl_links = [link for link in links if link.edge_type == EdgeType.ISL]

    assert len(isl_links) == 1
    assert isl_links[0].distance_km is not None
    assert isl_links[0].elevation_deg is None


def test_tle_candidate_links_feed_existing_topology_engine():
    pytest.importorskip("sgp4.api")
    source = TLESGP4Source.from_file(
        TLE_FIXTURE,
        ground_stations=(_ground_station(),),
        include_isl=True,
    )
    frame = source.frame_at(0.0)
    engine = SpatiotemporalTopologyEngine(
        satellites=frame.satellites,
        ground_stations=frame.ground_stations,
        min_elevation_deg=0.0,
        max_sgl_range_km=None,
        max_isl_range_km=None,
    )

    snapshot = engine.build_snapshot(
        time=frame.time,
        candidate_links=frame.candidate_links,
    )

    assert snapshot.node_count == len(frame.satellites) + len(frame.ground_stations)
    assert len(snapshot.edges) == len(frame.candidate_links)


def test_tle_sgp4_source_reports_clear_optional_dependency_error(monkeypatch):
    import quasar.scenarios.tle_sgp4 as tle_sgp4

    monkeypatch.setattr(tle_sgp4, "Satrec", None)
    source = TLESGP4Source(tle_lines=TLE_FIXTURE.read_text().splitlines())

    with pytest.raises(ImportError, match="optional 'sgp4' package"):
        source.frame_at(0.0)


def test_scenarios_module_has_no_runner_routing_events_metrics_or_simqn():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/scenarios").glob("*.py")
    )

    assert "def run(" not in source
    assert "compute_route" not in source
    assert "SDRouter" not in source
    assert "OOSDSPRouter" not in source
    assert "OOSMPRRouter" not in source
    assert "OOSEASRRouter" not in source
    assert "EventBridge" not in source
    assert "detect_events" not in source
    assert "MetricSummary" not in source
    assert "func_to_event" not in source
    assert "Simulator.add_event" not in source
    assert "100 ms polling" not in source
