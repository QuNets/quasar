"""Metric summary model for lightweight QUASAR runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from quasar.events.types import EventType


@dataclass
class MetricSummary:
    """Aggregated metrics reported by a QUASAR simulation run."""

    delivered_count: int = 0
    failed_count: int = 0
    request_count: int = 0
    total_events: int = 0
    available_edge_ratio: Optional[float] = None
    average_transmittance: Optional[float] = None
    average_cost: Optional[float] = None
    average_fidelity: Optional[float] = None
    average_success_probability: Optional[float] = None
    routing_success_rate: Optional[float] = None
    path_count: int = 0
    edge_record_count: int = 0
    event_counts: Dict[EventType, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.delivered_count < 0:
            raise ValueError("delivered_count must be non-negative")
        if self.failed_count < 0:
            raise ValueError("failed_count must be non-negative")
        if self.request_count < 0:
            raise ValueError("request_count must be non-negative")
        if self.total_events < 0:
            raise ValueError("total_events must be non-negative")
        if self.path_count < 0:
            raise ValueError("path_count must be non-negative")
        if self.edge_record_count < 0:
            raise ValueError("edge_record_count must be non-negative")

    @property
    def success_ratio(self) -> float:
        """Return delivered requests divided by total known requests."""

        denominator = self.request_count
        if denominator == 0:
            denominator = self.delivered_count + self.failed_count
        if denominator == 0:
            return 0.0
        return self.delivered_count / denominator

    @classmethod
    def from_logs(
        cls,
        event_log: Any = None,
        edge_trace: Any = None,
        path_trace: Any = None,
    ) -> "MetricSummary":
        """Build a summary from optional event, edge, and path logs."""

        event_counts = {}
        total_events = 0
        if event_log is not None:
            event_counts = event_log.count_by_type()
            total_events = event_log.total_count

        edge_summary = {}
        if edge_trace is not None:
            edge_summary = edge_trace.summary()

        path_summary = {}
        delivered_count = 0
        failed_count = 0
        if path_trace is not None:
            path_summary = path_trace.summary()
            delivered_count = sum(1 for record in path_trace.records if record.success)
            failed_count = len(path_trace.records) - delivered_count

        return cls(
            delivered_count=delivered_count,
            failed_count=failed_count,
            request_count=delivered_count + failed_count,
            total_events=total_events,
            available_edge_ratio=edge_summary.get("available_edge_ratio"),
            average_transmittance=edge_summary.get("average_transmittance"),
            average_cost=path_summary.get("average_cost"),
            average_fidelity=edge_summary.get("average_fidelity"),
            average_success_probability=edge_summary.get(
                "average_success_probability"
            ),
            routing_success_rate=path_summary.get("routing_success_rate"),
            path_count=path_summary.get("path_count", 0),
            edge_record_count=edge_summary.get("edge_record_count", 0),
            event_counts=event_counts,
        )

    def to_dict(self) -> dict:
        """Return summary values as a plain dictionary."""

        return {
            "delivered_count": self.delivered_count,
            "failed_count": self.failed_count,
            "request_count": self.request_count,
            "success_ratio": self.success_ratio,
            "event_counts": {
                event_type.value: count
                for event_type, count in self.event_counts.items()
            },
            "total_events": self.total_events,
            "available_edge_ratio": self.available_edge_ratio,
            "average_transmittance": self.average_transmittance,
            "average_cost": self.average_cost,
            "average_fidelity": self.average_fidelity,
            "average_success_probability": self.average_success_probability,
            "routing_success_rate": self.routing_success_rate,
            "path_count": self.path_count,
            "edge_record_count": self.edge_record_count,
        }

    def summary(self) -> dict:
        """Return a compact summary dictionary."""

        return self.to_dict()
