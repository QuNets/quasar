"""Base routing abstractions for QUASAR workloads."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence


@dataclass
class EntanglementRequest:
    """A request to distribute entanglement between two endpoints."""

    source: str
    destination: str
    created_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteResult:
    """Result returned by a QUASAR routing workload."""

    path: Sequence[str] = field(default_factory=tuple)
    success: bool = False
    cost: Optional[float] = None
    success_probability: Optional[float] = None
    fidelity: Optional[float] = None
    reason: Optional[str] = None


class Router(ABC):
    """Abstract router interface for QUASAR routing workloads."""

    name = "router"

    @abstractmethod
    def compute_route(self, graph: Any, request: EntanglementRequest, time: float) -> RouteResult:
        """Compute a route over a dynamic graph snapshot."""
        raise NotImplementedError
