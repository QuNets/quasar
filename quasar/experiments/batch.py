"""Batch helpers for small QUASAR experiment comparisons."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Tuple, Union

from quasar.experiments.cases import ExperimentCase
from quasar.experiments.config import ExperimentConfig
from quasar.experiments.diagnostics import storage_delay_summary
from quasar.experiments.result import ExperimentResult
from quasar.experiments.runner import QuasarExperimentRunner


ConfigOrCase = Union[ExperimentConfig, ExperimentCase]


def run_many(configs_or_cases: Iterable[ConfigOrCase]) -> Tuple[ExperimentResult, ...]:
    """Execute each config or case with the existing experiment runner."""

    return tuple(_execute_item(item) for item in configs_or_cases)


def result_summary_row(result: ExperimentResult) -> dict:
    """Return a compact row for text tables or notebooks."""

    summary = result.summary_dict()
    metadata = result.metadata
    delay_summary = storage_delay_summary(result)
    case_name = metadata.get("case", result.config.routing_algorithm.upper())
    route_attempts = len(result.route_results)
    route_successes = sum(1 for route in result.route_results if route.success)
    edge_storage_delay = _average(
        record.storage_delay for record in result.edge_trace.records
    )
    return {
        "case": case_name,
        "name": case_name,
        "architecture": result.config.architecture,
        "routing_algorithm": result.config.routing_algorithm,
        "route_attempts": route_attempts,
        "route_successes": route_successes,
        "routing_success_rate": summary.get("routing_success_rate"),
        "total_candidate_edges": metadata.get("total_candidate_edges"),
        "total_available_edges": metadata.get("total_available_edges"),
        "topology_available_edge_ratio": metadata.get(
            "topology_available_edge_ratio"
        ),
        "total_events": summary.get("total_events"),
        "average_transmittance": summary.get("average_transmittance"),
        "average_storage_delay": edge_storage_delay,
        "average_edge_storage_delay": delay_summary.get(
            "average_edge_storage_delay"
        ),
        "average_route_storage_delay": delay_summary.get(
            "average_route_storage_delay"
        ),
        "min_route_storage_delay": delay_summary.get("min_route_storage_delay"),
        "max_route_storage_delay": delay_summary.get("max_route_storage_delay"),
        "average_route_fidelity": delay_summary.get("average_route_fidelity"),
        "average_edge_fidelity": summary.get("average_fidelity"),
        "average_fidelity": summary.get("average_fidelity"),
        "storage_delay_source": metadata.get("storage_delay_source"),
        "storage_delay_policy": metadata.get("storage_delay_policy"),
    }


def results_summary_rows(results: Iterable[ExperimentResult]) -> Tuple[dict, ...]:
    """Return summary rows for a collection of experiment results."""

    return tuple(result_summary_row(result) for result in results)


def _execute_item(item: ConfigOrCase) -> ExperimentResult:
    if isinstance(item, ExperimentCase):
        result = QuasarExperimentRunner(item.config).execute()
        metadata = {
            **result.metadata,
            "case": item.name,
            "case_metadata": dict(item.metadata),
        }
        return replace(result, metadata=metadata)
    return QuasarExperimentRunner(item).execute()


def _average(values) -> float:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return 0.0
    return sum(numeric_values) / len(numeric_values)
