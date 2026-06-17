"""Tests for contact-window-age storage delay in experiments."""

from pathlib import Path

import pytest

from quasar.experiments import ExperimentConfig, QuasarExperimentRunner, WorkloadConfig


def _config(routing_algorithm="easr"):
    return ExperimentConfig(
        workload=WorkloadConfig(
            architecture="oos",
            routing_algorithm=routing_algorithm,
            storage_delay_policy="contact_window_age",
        ),
        time_points=(0.0, 1.0),
        planes=2,
        satellites_per_plane=2,
    )


def test_contact_window_age_storage_delay_policy_is_valid():
    workload = WorkloadConfig(storage_delay_policy="contact_window_age")

    assert workload.storage_delay_policy == "contact_window_age"


def test_invalid_storage_delay_policy_still_raises_value_error():
    with pytest.raises(ValueError):
        WorkloadConfig(storage_delay_policy="bad_policy")


def test_runner_records_contact_window_age_storage_delay_metadata():
    result = QuasarExperimentRunner(_config()).execute()

    assert result.metadata["storage_delay_source"] == (
        "sampled_contact_schedule_estimator"
    )
    assert result.metadata["storage_delay_policy"] == "contact_window_age"
    assert result.metadata["not_resource_reservation"] is True
    assert result.edge_trace.records
    assert any(
        record.storage_delay is not None and record.storage_delay > 0.0
        for record in result.edge_trace.records
    )
    assert all(
        record.metadata["storage_delay_source"]
        == "sampled_contact_schedule_estimator"
        for record in result.edge_trace.records
    )
    assert all(
        record.metadata["storage_delay_policy"] == "contact_window_age"
        for record in result.edge_trace.records
    )


def test_oos_easr_consumes_contact_window_age_storage_delay():
    result = QuasarExperimentRunner(_config("easr")).execute()

    assert len(result.route_results) == 2
    assert result.config.routing_algorithm == "easr"
    assert result.metadata["storage_delay_source"] == (
        "sampled_contact_schedule_estimator"
    )


def test_oos_mpr_runs_with_contact_window_age_storage_delay():
    result = QuasarExperimentRunner(_config("mpr")).execute()

    assert len(result.route_results) == 2
    assert result.config.routing_algorithm == "mpr"
    assert result.metadata["storage_delay_policy"] == "contact_window_age"


def test_experiment_storage_delay_changes_do_not_touch_routing_objective():
    source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "quasar/experiments/config.py",
            "quasar/experiments/runner.py",
        )
    )
    routing_source = Path("quasar/routing/easr.py").read_text(encoding="utf-8")

    assert "def run(" not in source
    assert "Simulator" not in source
    assert "func_to_event" not in source
    assert "resource reservation" not in source
    assert "queueing" not in source
    assert "route recomputation policy" not in source
    assert "contact_window_age" not in routing_source
