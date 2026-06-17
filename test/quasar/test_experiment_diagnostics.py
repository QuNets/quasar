"""Tests for experiment diagnostics helpers."""

from pathlib import Path
from types import SimpleNamespace

from quasar.experiments import (
    ExperimentConfig,
    QuasarExperimentRunner,
    WorkloadConfig,
    result_summary_row,
    result_diagnostics,
    route_diagnostic_rows,
    storage_delay_summary,
)


def _config(policy="zero_policy", routing_algorithm="easr"):
    return ExperimentConfig(
        workload=WorkloadConfig(
            architecture="oos",
            routing_algorithm=routing_algorithm,
            storage_delay_policy=policy,
        ),
        time_points=(0.0, 300.0, 600.0, 900.0, 1200.0, 1500.0),
        planes=6,
        satellites_per_plane=10,
    )


def test_route_diagnostics_handle_success_and_failure_routes():
    records = (
        SimpleNamespace(
            time=0.0,
            architecture="oos",
            algorithm="easr",
            success=True,
            path=("A", "B"),
            storage_delay=0.0,
            success_probability=0.5,
            fidelity=0.99,
            metadata={"objective_score": 0.5},
        ),
        SimpleNamespace(
            time=1.0,
            architecture="oos",
            algorithm="easr",
            success=False,
            path=(),
            storage_delay=None,
            success_probability=None,
            fidelity=None,
            metadata={},
        ),
    )
    route_results = (
        SimpleNamespace(success=True, reason=None, metadata={"objective_score": 0.5}),
        SimpleNamespace(success=False, reason="no path", metadata={}),
    )
    result = SimpleNamespace(
        path_trace=SimpleNamespace(records=records),
        route_results=route_results,
    )

    rows = route_diagnostic_rows(result)

    assert rows[0]["success"] is True
    assert rows[0]["hop_count"] == 1
    assert rows[0]["objective_score"] == 0.5
    assert rows[1]["success"] is False
    assert rows[1]["failure_reason"] == "no path"


def test_missing_diagnostic_fields_return_unknown_or_none():
    result = SimpleNamespace(
        path_trace=SimpleNamespace(records=(SimpleNamespace(time=0.0),)),
        route_results=(),
    )

    row = route_diagnostic_rows(result)[0]

    assert row["selected_path"] == ()
    assert row["route_storage_delay"] is None
    assert row["objective_score"] is None
    assert row["failure_reason"] == "unknown"


def test_zero_policy_average_route_delay_is_zero_or_none():
    result = QuasarExperimentRunner(_config("zero_policy")).execute()
    summary = storage_delay_summary(result)

    assert summary["average_edge_storage_delay"] == 0.0
    assert summary["average_route_storage_delay"] in (0.0, None)


def test_contact_window_age_has_nonzero_edge_delay_and_summary_fields():
    result = QuasarExperimentRunner(_config("contact_window_age")).execute()
    summary = storage_delay_summary(result)
    row = result_summary_row(result)

    assert summary["average_edge_storage_delay"] > 0.0
    assert summary["average_route_storage_delay"] is not None
    assert row["average_edge_storage_delay"] == summary["average_edge_storage_delay"]
    assert row["average_route_storage_delay"] == (
        summary["average_route_storage_delay"]
    )
    assert "average_route_storage_delay" in row
    assert "min_route_storage_delay" in row
    assert "max_route_storage_delay" in row
    assert "average_route_fidelity" in row
    assert row["storage_delay_policy"] == "contact_window_age"


def test_result_diagnostics_do_not_modify_routing_decisions():
    result = QuasarExperimentRunner(_config("contact_window_age", "mpr")).execute()
    before = tuple(route.path_tuple for route in result.route_results)

    diagnostics = result_diagnostics(result)

    after = tuple(route.path_tuple for route in result.route_results)
    assert before == after
    assert "routes" in diagnostics
    assert "storage_delay" in diagnostics


def test_contact_window_age_route_diagnostics_attribute_successful_mpr_path():
    result = QuasarExperimentRunner(_config("contact_window_age", "mpr")).execute()
    rows = route_diagnostic_rows(result)
    successful_rows = [row for row in rows if row["success"]]

    assert any(row["route_storage_delay"] > 0.0 for row in successful_rows)
    assert any(row["route_fidelity"] < 0.99 for row in successful_rows)
    assert all(
        row["hop_count"] == len(row["selected_path"]) - 1
        for row in successful_rows
    )


def test_zero_policy_route_diagnostics_keep_zero_route_delay():
    result = QuasarExperimentRunner(_config("zero_policy", "mpr")).execute()
    rows = route_diagnostic_rows(result)
    successful_rows = [row for row in rows if row["success"]]

    assert successful_rows
    assert all(row["route_storage_delay"] == 0.0 for row in successful_rows)


def test_diagnostics_helpers_have_no_out_of_scope_execution_features():
    source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "quasar/experiments/diagnostics.py",
            "quasar/experiments/batch.py",
        )
    )

    assert "def run(" not in source
    assert "Simulator" not in source
    assert "func_to_event" not in source
    assert "resource reservation" not in source
    assert "queueing" not in source
    assert "plotting" not in source
