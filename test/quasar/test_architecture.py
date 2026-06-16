"""Tests for QUASAR hardware architecture abstractions."""

from pathlib import Path

from quasar.architecture import (
    ArchitectureMode,
    OnOrbitStitchingArchitecture,
    SimultaneousDownlinkArchitecture,
)
from quasar.channel.models import EdgeType
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


def test_sd_feasible_with_common_satellite_dual_downlink():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.5),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, transmittance=0.25),
        ),
    )

    results = SimultaneousDownlinkArchitecture().find_opportunities(snapshot, ("gs-a", "gs-b"))

    assert len(results) == 1
    assert results[0].feasible
    assert results[0].architecture == ArchitectureMode.SIMULTANEOUS_DOWNLINK


def test_sd_infeasible_without_common_satellite():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "sat-2", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.5),
            LinkState(("sat-2", "gs-b"), EdgeType.SGL, transmittance=0.25),
        ),
    )

    results = SimultaneousDownlinkArchitecture().find_opportunities(snapshot, ("gs-a", "gs-b"))

    assert results == []


def test_sd_storage_delay_is_zero_and_joint_transmittance_is_product():
    snapshot = TopologySnapshot(
        time=0.0,
        nodes=("sat-1", "gs-a", "gs-b"),
        edges=(
            LinkState(("sat-1", "gs-a"), EdgeType.SGL, transmittance=0.4),
            LinkState(("sat-1", "gs-b"), EdgeType.SGL, transmittance=0.5),
        ),
    )

    result = SimultaneousDownlinkArchitecture().find_opportunities(snapshot, ("gs-a", "gs-b"))[0]

    assert result.storage_delay == 0.0
    assert result.success_probability == 0.4 * 0.5


def test_sd_does_not_import_memory_decoherence():
    source = Path("quasar/architecture/simultaneous_downlink.py").read_text(encoding="utf-8")

    assert "fidelity_after_storage" not in source
    assert "is_fidelity_feasible" not in source
    assert "quasar.memory" not in source


def test_oos_storage_delay_reduces_fidelity():
    architecture = OnOrbitStitchingArchitecture(coherence_time=0.1, fidelity_threshold=0.0)

    short = architecture.evaluate_stitching_opportunity([0.5], storage_delay=0.01)
    long = architecture.evaluate_stitching_opportunity([0.5], storage_delay=0.2)

    assert long.fidelity < short.fidelity


def test_oos_low_fidelity_is_infeasible():
    architecture = OnOrbitStitchingArchitecture(coherence_time=0.1, fidelity_threshold=0.9)

    result = architecture.evaluate_stitching_opportunity([0.5], storage_delay=0.2)

    assert not result.feasible
    assert result.reason == "fidelity below threshold"


def test_oos_high_fidelity_is_feasible():
    architecture = OnOrbitStitchingArchitecture(coherence_time=1.0, fidelity_threshold=0.75)

    result = architecture.evaluate_stitching_opportunity([0.5, 0.5], storage_delay=0.01)

    assert result.feasible
    assert result.success_probability == 0.25


def test_sd_and_oos_are_independent_implementation_files():
    assert SimultaneousDownlinkArchitecture.__module__.endswith("simultaneous_downlink")
    assert OnOrbitStitchingArchitecture.__module__.endswith("on_orbit_stitching")


def test_stage5_does_not_implement_routing_events_or_run_loop():
    files = [
        Path("quasar/architecture/base.py"),
        Path("quasar/architecture/simultaneous_downlink.py"),
        Path("quasar/architecture/on_orbit_stitching.py"),
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)

    assert "compute_route" not in source
    assert "EventBridge" not in source
    assert "def run(" not in source
    assert "ROUTE_RECOMPUTE" not in source
