"""Tests for sampled contact timing helpers."""

from pathlib import Path

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.scenarios import ScenarioFrame, TraceReplaySource
from quasar.timing import (
    ContactSchedule,
    ContactWindow,
    StorageDelayEstimator,
    canonical_edge_key,
)


def _nodes():
    return (
        Satellite("SAT-1"),
        GroundStation("GS-A", latitude_deg=0.0, longitude_deg=0.0),
    )


def _link(time, elevation_deg):
    return LinkState(
        endpoints=("SAT-1", "GS-A"),
        edge_type=EdgeType.SGL,
        distance_km=500.0,
        elevation_deg=elevation_deg,
        updated_at=time,
    )


def _source_with_gap():
    satellite, station = _nodes()
    frames = {
        0.0: ScenarioFrame(
            time=0.0,
            satellites=(satellite,),
            ground_stations=(station,),
            candidate_links=(_link(0.0, 30.0),),
        ),
        1.0: ScenarioFrame(
            time=1.0,
            satellites=(satellite,),
            ground_stations=(station,),
            candidate_links=(_link(1.0, 35.0),),
        ),
        2.0: ScenarioFrame(
            time=2.0,
            satellites=(satellite,),
            ground_stations=(station,),
            candidate_links=(_link(2.0, 5.0),),
        ),
        3.0: ScenarioFrame(
            time=3.0,
            satellites=(satellite,),
            ground_stations=(station,),
            candidate_links=(_link(3.0, 40.0),),
        ),
    }
    return TraceReplaySource(frames=frames)


def test_contact_window_contains_and_duration():
    window = ContactWindow(
        endpoints=("SAT-1", "GS-A"),
        edge_type=EdgeType.SGL,
        start_time=1.0,
        end_time=3.0,
        sample_times=(1.0, 2.0, 3.0),
    )

    assert window.contains(2.0)
    assert not window.contains(4.0)
    assert window.duration == 2.0


def test_canonical_edge_key_is_order_independent():
    assert canonical_edge_key(("SAT-1", "GS-A")) == canonical_edge_key(
        ("GS-A", "SAT-1")
    )


def test_contact_schedule_builds_windows_from_explicit_time_grid():
    schedule = ContactSchedule.from_source(
        _source_with_gap(),
        time_points=(0.0, 1.0, 2.0, 3.0),
        min_elevation_deg=15.0,
    )

    windows = schedule.windows_for(("SAT-1", "GS-A"))

    assert len(windows) == 2
    assert windows[0].start_time == 0.0
    assert windows[0].end_time == 1.0
    assert windows[0].sample_times == (0.0, 1.0)
    assert windows[1].start_time == 3.0
    assert windows[1].end_time == 3.0


def test_next_contact_time_handles_active_future_and_missing_contacts():
    schedule = ContactSchedule.from_source(
        _source_with_gap(),
        time_points=(0.0, 1.0, 2.0, 3.0),
        min_elevation_deg=15.0,
    )

    assert schedule.active_window(("GS-A", "SAT-1"), 0.5) is not None
    assert schedule.next_contact_time(("SAT-1", "GS-A"), 0.5) == 0.5
    assert schedule.next_contact_time(("SAT-1", "GS-A"), 2.5) == 3.0
    assert schedule.next_contact_time(("SAT-1", "GS-A"), 4.0) is None


def test_storage_delay_estimator_returns_non_negative_delay():
    schedule = ContactSchedule.from_source(
        _source_with_gap(),
        time_points=(0.0, 1.0, 2.0, 3.0),
        min_elevation_deg=15.0,
    )
    estimator = StorageDelayEstimator(schedule)

    assert estimator.estimate_edge_delay(("SAT-1", "GS-A"), 0.5) == 0.0
    assert estimator.estimate_edge_delay(("SAT-1", "GS-A"), 2.5) == 0.5
    assert estimator.estimate_edge_delay(("SAT-1", "GS-A"), 4.0) is None
    assert estimator.estimate_path_delay(("SAT-1", "GS-A"), 2.5) == 0.5


def test_contact_window_age_delay_mode_is_sampled_window_age():
    schedule = ContactSchedule.from_source(
        _source_with_gap(),
        time_points=(0.0, 1.0, 2.0, 3.0),
        min_elevation_deg=15.0,
    )
    estimator = StorageDelayEstimator(schedule)

    active_delay = estimator.estimate_edge_delay(
        ("SAT-1", "GS-A"),
        0.5,
        mode="contact_window_age",
    )
    future_delay = estimator.estimate_edge_delay(
        ("SAT-1", "GS-A"),
        2.5,
        mode="contact_window_age",
    )

    assert active_delay == 0.5
    assert future_delay == 0.5
    assert active_delay >= 0.0
    assert future_delay >= 0.0
    assert (
        estimator.estimate_edge_delay(
            ("SAT-1", "GS-A"),
            4.0,
            mode="contact_window_age",
        )
        is None
    )


def test_storage_delay_estimator_metadata_is_explicit():
    estimator = StorageDelayEstimator(
        ContactSchedule.from_source(
            _source_with_gap(),
            time_points=(0.0, 1.0, 2.0, 3.0),
            min_elevation_deg=15.0,
        )
    )

    assert (
        estimator.metadata["storage_delay_source"]
        == "sampled_contact_schedule_estimator"
    )
    assert estimator.metadata["storage_delay_policy"] == "contact_window_age"
    assert estimator.metadata["not_resource_reservation"] is True


def test_timing_module_has_no_out_of_scope_execution_features():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/timing").glob("*.py")
    )

    assert "def run(" not in source
    assert "Simulator" not in source
    assert "func_to_event" not in source
    assert "route recomputation" not in source
    assert "new routing algorithm" not in source
    assert "scheduler" not in source
