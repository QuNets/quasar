"""Sampled contact-window models for QUASAR timing estimates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Tuple

from quasar.channel.models import EdgeType


def canonical_edge_key(edge_or_endpoints: Any) -> Tuple[str, str]:
    """Return an order-independent key for a two-endpoint link."""

    endpoints = getattr(edge_or_endpoints, "endpoints", edge_or_endpoints)
    endpoints = tuple(endpoints)
    if len(endpoints) != 2:
        raise ValueError("edge key requires exactly two endpoints")
    first, second = endpoints
    if not first or not second:
        raise ValueError("edge endpoints must be non-empty")
    if first == second:
        raise ValueError("edge endpoints must be distinct")
    return tuple(sorted((first, second)))


@dataclass(frozen=True)
class ContactWindow:
    """A sampled contact interval, not a continuous high-precision orbit window."""

    endpoints: Tuple[str, str]
    edge_type: EdgeType
    start_time: float
    end_time: float
    sample_times: Iterable[float] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        endpoints = canonical_edge_key(self.endpoints)
        sample_times = tuple(self.sample_times)
        if self.start_time < 0:
            raise ValueError("start_time must be non-negative")
        if self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        if any(time < 0 for time in sample_times):
            raise ValueError("sample_times must be non-negative")
        if tuple(sorted(sample_times)) != sample_times:
            raise ValueError("sample_times must be sorted")
        object.__setattr__(self, "endpoints", endpoints)
        object.__setattr__(self, "sample_times", sample_times)

    @property
    def duration(self) -> float:
        """Return the sampled window duration in seconds."""

        return self.end_time - self.start_time

    def contains(self, time: float) -> bool:
        """Return whether time is inside this sampled window."""

        return self.start_time <= time <= self.end_time
