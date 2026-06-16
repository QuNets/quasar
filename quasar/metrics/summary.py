"""Metric summary model for lightweight QUASAR runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from quasar.events.types import EventType


@dataclass
class MetricSummary:
    """Aggregated metrics reported by a QUASAR simulation run."""

    delivered_count: int = 0
    failed_count: int = 0
    request_count: int = 0
    average_cost: Optional[float] = None
    average_fidelity: Optional[float] = None
    average_success_probability: Optional[float] = None
    event_counts: Dict[EventType, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.delivered_count < 0:
            raise ValueError("delivered_count must be non-negative")
        if self.failed_count < 0:
            raise ValueError("failed_count must be non-negative")
        if self.request_count < 0:
            raise ValueError("request_count must be non-negative")

    @property
    def success_ratio(self) -> float:
        """Return delivered requests divided by total known requests."""

        denominator = self.request_count
        if denominator == 0:
            denominator = self.delivered_count + self.failed_count
        if denominator == 0:
            return 0.0
        return self.delivered_count / denominator
