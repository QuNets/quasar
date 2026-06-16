"""Metric sample models for QUASAR traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MetricSample:
    """A point-in-time snapshot of selected QUASAR metrics."""

    time: float
    available_edge_ratio: Optional[float] = None
    average_transmittance: Optional[float] = None
    average_success_probability: Optional[float] = None
    average_fidelity: Optional[float] = None
    routing_success_rate: Optional[float] = None
    event_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")
        if self.event_count < 0:
            raise ValueError("event_count must be non-negative")
        _validate_optional_probability(
            self.available_edge_ratio,
            "available_edge_ratio",
        )
        _validate_optional_probability(
            self.average_transmittance,
            "average_transmittance",
        )
        _validate_optional_probability(
            self.average_success_probability,
            "average_success_probability",
        )
        _validate_optional_probability(self.average_fidelity, "average_fidelity")
        _validate_optional_probability(
            self.routing_success_rate,
            "routing_success_rate",
        )


def _validate_optional_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
