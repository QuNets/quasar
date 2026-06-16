"""Minimal metric summary model for QUASAR runs."""

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
