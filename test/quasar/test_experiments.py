"""Tests for paper-aligned QUASAR experiment scaffolds."""

from pathlib import Path

import pytest

from quasar.experiments import (
    BaselineSimulationConfig,
    ExperimentConfig,
    FixedPairWorkload,
    QuasarExperimentRunner,
    WorkloadConfig,
    houston_washington_pair,
)
from quasar.experiments.result import ExperimentResult
from quasar.routing import EntanglementRequest


def test_baseline_parameters_match_paper_direction():
    baseline = BaselineSimulationConfig()

    assert baseline.altitude_km == 500.0
    assert baseline.inclination_deg == 53.0
    assert baseline.dt == 0.1
    assert baseline.min_elevation_deg == 15.0
    assert baseline.eta0 == 1e-3
    assert baseline.alpha == 0.15
    assert baseline.h0_km == 20.0
    assert baseline.kappa == 0.85
    assert baseline.zeta_swap == 0.60
    assert baseline.f0 == 0.99
    assert baseline.fidelity_threshold == 0.75
    assert baseline.tau_c == 0.1


def test_houston_washington_coordinates_are_correct():
    houston, washington = houston_washington_pair()

    assert houston.name == "Houston"
    assert houston.latitude_deg == 29.7604
    assert houston.longitude_deg == -95.3698
    assert washington.name == "Washington-DC"
    assert washington.latitude_deg == 38.9072
    assert washington.longitude_deg == -77.0369


def test_experiment_config_default_is_small_explicit_time_points():
    config = ExperimentConfig()

    assert config.time_points == (0.0, 0.1, 0.2)
    assert max(config.time_points) == 0.2
    assert config.planes == 4
    assert config.satellites_per_plane == 5
    assert config.architecture == "oos"
    assert config.routing_algorithm == "easr"


def test_fixed_pair_workload_generates_entanglement_request():
    houston, washington = houston_washington_pair()
    workload = FixedPairWorkload(houston, washington)

    request = workload.request_at(0.1)

    assert isinstance(request, EntanglementRequest)
    assert request.source == "Houston"
    assert request.destination == "Washington-DC"
    assert request.created_at == 0.1


def test_experiment_runner_execute_returns_result_with_traces():
    result = QuasarExperimentRunner(ExperimentConfig()).execute()

    assert isinstance(result, ExperimentResult)
    assert len(result.frames) == 3
    assert len(result.snapshots) == 3
    assert len(result.route_results) == 3
    assert result.event_log is not None
    assert result.edge_trace is not None
    assert result.path_trace is not None
    assert result.summary is not None
    assert result.summary.path_count == 3
    assert result.summary.edge_record_count == len(result.edge_trace.records)
    assert result.metadata["scenario_source"] == "WalkerDeltaLiteSource"
    assert "topology_available_edge_ratio" in result.metadata
    assert result.to_dict()["total_candidate_edges"] == (
        result.metadata["total_candidate_edges"]
    )


def test_topology_edge_ratio_is_based_on_snapshots_not_edge_trace():
    result = QuasarExperimentRunner(ExperimentConfig()).execute()
    counts = result.metadata["snapshot_edge_counts"]
    total_candidate_edges = sum(len(snapshot.edges) for snapshot in result.snapshots)
    total_available_edges = sum(
        len(snapshot.available_edges) for snapshot in result.snapshots
    )

    assert len(counts) == len(result.snapshots)
    assert result.metadata["total_candidate_edges"] == total_candidate_edges
    assert result.metadata["total_available_edges"] == total_available_edges
    assert result.metadata["topology_available_edge_ratio"] == pytest.approx(
        total_available_edges / total_candidate_edges
    )
    assert result.metadata["total_available_edges"] == len(result.edge_trace.records)
    assert result.metadata["total_candidate_edges"] > len(result.edge_trace.records)
    assert result.metadata["topology_available_edge_ratio"] < (
        result.summary.available_edge_ratio
    )


@pytest.mark.parametrize("algorithm", ("dsp", "mpr", "easr"))
def test_oos_workloads_execute(algorithm):
    config = ExperimentConfig(
        workload=WorkloadConfig(
            architecture="oos",
            routing_algorithm=algorithm,
        ),
        time_points=(0.0,),
    )

    result = QuasarExperimentRunner(config).execute()

    assert len(result.route_results) == 1
    assert result.config.routing_algorithm == algorithm


def test_sd_workload_uses_sd_router_and_zero_storage_delay():
    config = ExperimentConfig(
        workload=WorkloadConfig(architecture="sd", routing_algorithm="sd"),
        time_points=(0.0,),
    )

    result = QuasarExperimentRunner(config).execute()

    assert len(result.route_results) == 1
    assert result.route_results[0].storage_delay in (0.0, None)
    assert result.metadata["storage_delay_source"] == "zero_policy"


def test_illegal_architecture_router_combinations_raise_value_error():
    with pytest.raises(ValueError):
        WorkloadConfig(architecture="sd", routing_algorithm="easr")

    with pytest.raises(ValueError):
        WorkloadConfig(architecture="oos", routing_algorithm="sd")

    with pytest.raises(ValueError):
        WorkloadConfig(architecture="bad", routing_algorithm="easr")


def test_synthetic_storage_delay_is_labeled():
    config = ExperimentConfig(
        workload=WorkloadConfig(
            architecture="oos",
            routing_algorithm="easr",
            storage_delay_policy="synthetic_demo",
            synthetic_storage_delay=0.01,
        ),
        time_points=(0.0,),
    )

    result = QuasarExperimentRunner(config).execute()

    assert result.metadata["storage_delay_source"] == "synthetic_demo_not_contact_schedule"
    assert result.path_trace.records[0].metadata["storage_delay_source"] == (
        "synthetic_demo_not_contact_schedule"
    )


def test_experiments_module_has_no_out_of_scope_execution_features():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/experiments").glob("*.py")
    )

    assert "def run(" not in source
    assert "while" not in source
    assert "Simulator" not in source
    assert "func_to_event" not in source
    assert "plotting" not in source
    assert "24h" not in source
