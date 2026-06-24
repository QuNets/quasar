"""Base routing abstractions for QUASAR workloads."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence, Tuple


def _validate_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass
class EntanglementRequest:
    """A request to distribute entanglement between two endpoints."""

    source: str
    destination: str
    created_at: float = 0.0
    deadline: Optional[float] = None
    target_fidelity: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source must be a non-empty string")
        if not self.destination:
            raise ValueError("destination must be a non-empty string")
        if self.source == self.destination:
            raise ValueError("source and destination must be distinct")
        if self.created_at < 0:
            raise ValueError("created_at must be non-negative")
        if self.deadline is not None and self.deadline < self.created_at:
            raise ValueError("deadline must be greater than or equal to created_at")
        _validate_probability(self.target_fidelity, "target_fidelity")


@dataclass
class RouteResult:
    """Result returned by a QUASAR routing workload."""

    path: Sequence[str] = field(default_factory=tuple)
    success: bool = False
    cost: Optional[float] = None
    success_probability: Optional[float] = None
    fidelity: Optional[float] = None
    storage_delay: Optional[float] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.path = tuple(self.path)
        for idx, node in enumerate(self.path):
            if not node:
                raise ValueError(f"path[{idx}] must be a non-empty string")
        if self.cost is not None and self.cost < 0:
            raise ValueError("cost must be non-negative")
        _validate_probability(self.success_probability, "success_probability")
        _validate_probability(self.fidelity, "fidelity")
        if self.storage_delay is not None and self.storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")

    @property
    def hop_count(self) -> int:
        """Return the number of hops in the selected route."""

        if len(self.path) < 2:
            return 0
        return len(self.path) - 1

    @property
    def path_tuple(self) -> Tuple[str, ...]:
        """Return the route path as an immutable tuple."""

        return tuple(self.path)


class Router(ABC):
    """Abstract router interface for QUASAR routing workloads."""

    name = "router"

    @abstractmethod
    def compute_route(self, graph: Any, request: EntanglementRequest, time: float) -> RouteResult:
        """Compute a route over a dynamic graph snapshot."""
        raise NotImplementedError
