"""Tests for experiment case and batch helpers."""

from pathlib import Path
from dataclasses import replace

from quasar.experiments import (
    DEFAULT_BATCH_TIME_POINTS,
    ExperimentCase,
    ExperimentConfig,
    ExperimentResult,
    WorkloadConfig,
    results_summary_rows,
    routing_baseline_cases,
    run_many,
)


def test_routing_baseline_cases_define_oos_baselines():
    cases = routing_baseline_cases()

    assert len(cases) == 3
    assert all(isinstance(case, ExperimentCase) for case in cases)
    assert tuple(case.name for case in cases) == ("OOS-DSP", "OOS-MPR", "OOS-EASR")
    assert tuple(case.config.routing_algorithm for case in cases) == (
        "dsp",
        "mpr",
        "easr",
    )
    assert all(case.config.architecture == "oos" for case in cases)
    assert all(
        case.config.workload.storage_delay_policy == "zero_policy"
        for case in cases
    )


def test_routing_baseline_cases_use_houston_washington_smoke_config():
    cases = routing_baseline_cases()

    assert all(case.config.controlled_pair.source_name == "Houston" for case in cases)
    assert all(
        case.config.controlled_pair.destination_name == "Washington-DC"
        for case in cases
    )
    assert all(case.config.time_points == DEFAULT_BATCH_TIME_POINTS for case in cases)
    assert all(case.config.planes == 6 for case in cases)
    assert all(case.config.satellites_per_plane == 10 for case in cases)


def test_run_many_returns_tuple_of_experiment_results():
    cases = routing_baseline_cases(time_points=(0.0,), planes=2, satellites_per_plane=2)

    results = run_many(cases)

    assert isinstance(results, tuple)
    assert len(results) == 3
    assert all(isinstance(result, ExperimentResult) for result in results)
    assert tuple(result.metadata["case"] for result in results) == (
        "OOS-DSP",
        "OOS-MPR",
        "OOS-EASR",
    )


def test_run_many_accepts_configs_and_empty_input():
    config = ExperimentConfig(
        workload=WorkloadConfig(architecture="oos", routing_algorithm="dsp"),
        time_points=(0.0,),
        planes=2,
        satellites_per_plane=2,
    )

    assert run_many(()) == ()
    results = run_many((config,))

    assert len(results) == 1
    assert results[0].config.routing_algorithm == "dsp"


def test_results_summary_rows_include_batch_fields():
    cases = routing_baseline_cases(time_points=(0.0,), planes=2, satellites_per_plane=2)
    rows = results_summary_rows(run_many(cases))

    assert len(rows) == 3
    for row in rows:
        assert row["case"].startswith("OOS-")
        assert row["name"] == row["case"]
        assert row["architecture"] == "oos"
        assert row["routing_algorithm"] in ("dsp", "mpr", "easr")
        assert "route_attempts" in row
        assert "route_successes" in row
        assert "routing_success_rate" in row
        assert "total_candidate_edges" in row
        assert "total_available_edges" in row
        assert "topology_available_edge_ratio" in row
        assert "total_events" in row
        assert row["storage_delay_source"] == "zero_policy"


def test_summary_rows_include_contact_delay_fields():
    case = routing_baseline_cases(time_points=(0.0, 1.0), planes=2, satellites_per_plane=2)[0]
    config = replace(
        case.config,
        workload=WorkloadConfig(
            architecture="oos",
            routing_algorithm=case.config.routing_algorithm,
            storage_delay_policy="contact_window_age",
        ),
    )
    result = run_many((ExperimentCase("OOS-DSP", config),))[0]
    row = results_summary_rows((result,))[0]

    assert row["storage_delay_source"] == "sampled_contact_schedule_estimator"
    assert "average_storage_delay" in row
    assert "average_route_storage_delay" in row
    assert row["average_storage_delay"] > 0.0


def test_batch_helpers_have_no_out_of_scope_execution_features():
    source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "quasar/experiments/cases.py",
            "quasar/experiments/batch.py",
        )
    )

    assert "def run(" not in source
    assert "Simulator" not in source
    assert "func_to_event" not in source
    assert "plotting" not in source
    assert "24h" not in source
    assert "contact schedule" not in source.lower()
