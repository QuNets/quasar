"""Read-only diagnostics for QUASAR experiment results."""

from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple

from quasar.experiments.result import ExperimentResult
from quasar.memory.decoherence import fidelity_after_storage


def route_diagnostic_rows(result: ExperimentResult) -> Tuple[dict, ...]:
    """Return per-route diagnostic rows without changing routing decisions."""

    rows = []
    route_results = tuple(result.route_results)
    for index, record in enumerate(result.path_trace.records):
        route_result = route_results[index] if index < len(route_results) else None
        metadata = _metadata(record, route_result)
        selected_path = tuple(getattr(record, "path", ()) or ())
        computed = _computed_route_diagnostics(result, record, selected_path)
        route_storage_delay = _diagnostic_value(
            metadata.get("route_storage_delay"),
            getattr(record, "storage_delay", None),
            computed.get("route_storage_delay"),
        )
        route_success_probability = _diagnostic_value(
            metadata.get("route_success_probability"),
            getattr(record, "success_probability", None),
            computed.get("route_success_probability"),
        )
        route_fidelity = _diagnostic_value(
            metadata.get("route_fidelity"),
            getattr(record, "fidelity", None),
            computed.get("route_fidelity"),
        )
        rows.append(
            {
                "time": getattr(record, "time", None),
                "architecture": getattr(record, "architecture", None),
                "routing_algorithm": getattr(record, "algorithm", None),
                "success": bool(getattr(record, "success", False)),
                "selected_path": selected_path,
                "opportunity": metadata.get("selected_opportunity"),
                "hop_count": metadata.get("hop_count", _hop_count(selected_path)),
                "route_storage_delay": route_storage_delay,
                "route_success_probability": route_success_probability,
                "route_fidelity": route_fidelity,
                "objective_score": metadata.get("objective_score"),
                "failure_reason": _failure_reason(route_result),
            }
        )
    return tuple(rows)


def storage_delay_summary(result: ExperimentResult) -> dict:
    """Return edge-level and route-level storage-delay diagnostics."""

    edge_delays = tuple(
        record.storage_delay
        for record in result.edge_trace.records
        if record.storage_delay is not None
    )
    rows = route_diagnostic_rows(result)
    route_delays = tuple(
        row["route_storage_delay"]
        for row in rows
        if row["route_storage_delay"] is not None
    )
    route_fidelities = tuple(
        row["route_fidelity"]
        for row in rows
        if row["route_fidelity"] is not None
    )
    fidelity_feasible_count = sum(
        1
        for row in rows
        if row["route_fidelity"] is not None and bool(row["success"])
    )
    fidelity_infeasible_count = sum(
        1
        for row in rows
        if row["route_fidelity"] is not None and not bool(row["success"])
    )
    return {
        "average_edge_storage_delay": _average(edge_delays),
        "average_route_storage_delay": _average(route_delays),
        "min_route_storage_delay": _minimum(route_delays),
        "max_route_storage_delay": _maximum(route_delays),
        "average_route_fidelity": _average(route_fidelities),
        "successful_route_count": sum(
            1 for record in result.path_trace.records if record.success
        ),
        "failed_route_count": sum(
            1 for record in result.path_trace.records if not record.success
        ),
        "fidelity_feasible_count": fidelity_feasible_count,
        "fidelity_infeasible_count": fidelity_infeasible_count,
        "storage_delay_source": result.metadata.get("storage_delay_source"),
        "storage_delay_policy": result.metadata.get("storage_delay_policy"),
    }


def result_diagnostics(result: ExperimentResult) -> dict:
    """Return route rows plus a compact storage-delay summary."""

    return {
        "routes": route_diagnostic_rows(result),
        "storage_delay": storage_delay_summary(result),
    }


def _metadata(record: Any, route_result: Any) -> dict:
    metadata = dict(getattr(route_result, "metadata", {}) or {})
    metadata.update(getattr(record, "metadata", {}) or {})
    return metadata


def _failure_reason(route_result: Any) -> str:
    reason = getattr(route_result, "reason", None)
    if reason:
        return reason
    if route_result is not None and bool(getattr(route_result, "success", False)):
        return ""
    return "unknown"


def _computed_route_diagnostics(
    result: ExperimentResult,
    record: Any,
    selected_path: Tuple[str, ...],
) -> dict:
    if len(selected_path) < 2:
        return {}
    request = getattr(record, "request", None)
    request_metadata = getattr(request, "metadata", {}) or {}
    edge_attributes = request_metadata.get("edge_attributes", ())
    edge_map = _edge_attribute_map(edge_attributes)
    storage_delay = 0.0
    success_probability = 1.0
    for first, second in zip(selected_path, selected_path[1:]):
        edge = edge_map.get((first, second))
        if edge is None:
            return {}
        storage_delay += getattr(edge, "storage_delay", None) or 0.0
        probability = getattr(edge, "success_probability", None)
        if probability is None:
            probability = getattr(edge, "transmittance", None)
        if probability is not None:
            success_probability *= probability
    baseline = getattr(getattr(result, "config", None), "baseline", None)
    f0 = getattr(baseline, "f0", 0.99)
    tau_c = getattr(baseline, "tau_c", 0.1)
    return {
        "route_storage_delay": storage_delay,
        "route_success_probability": success_probability,
        "route_fidelity": fidelity_after_storage(storage_delay, f0=f0, tau_c=tau_c),
    }


def _edge_attribute_map(edge_attributes: Iterable[Any]) -> dict:
    edge_map = {}
    for edge in edge_attributes:
        endpoints = getattr(edge, "endpoints", None)
        if endpoints is None or len(endpoints) != 2:
            continue
        first, second = endpoints
        edge_map[(first, second)] = edge
        edge_map[(second, first)] = edge
    return edge_map


def _diagnostic_value(metadata_value, record_value, computed_value):
    if computed_value is None:
        if metadata_value is not None:
            return metadata_value
        return record_value
    if metadata_value is None and record_value is None:
        return computed_value
    value = metadata_value if metadata_value is not None else record_value
    if value == 0.0 and computed_value > 0.0:
        return computed_value
    return value


def _hop_count(path: Iterable[str]) -> int:
    path = tuple(path)
    if len(path) < 2:
        return 0
    return len(path) - 1


def _average(values: Iterable[Optional[float]]) -> Optional[float]:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _minimum(values: Iterable[Optional[float]]) -> Optional[float]:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return min(numeric_values)


def _maximum(values: Iterable[Optional[float]]) -> Optional[float]:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return max(numeric_values)
