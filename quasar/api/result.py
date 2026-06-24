"""Result models for user-facing QUASAR API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

from quasar.channel.models import EdgeAttributes
from quasar.topology.graph import TopologySnapshot


@dataclass(frozen=True)
class QuasarStepResult:
    """Result returned by one QUASAR single-step simulation call."""

    time: float
    snapshot: TopologySnapshot
    edge_attributes: Iterable[EdgeAttributes] = field(default_factory=tuple)
    available_edge_count: int = field(init=False)
    total_edge_count: int = field(init=False)

    def __post_init__(self) -> None:
        edge_attributes = tuple(self.edge_attributes)
        object.__setattr__(self, "edge_attributes", edge_attributes)
        object.__setattr__(self, "available_edge_count", len(self.snapshot.available_edges))
        object.__setattr__(self, "total_edge_count", len(self.snapshot.edges))

    def summary(self) -> Dict[str, float]:
        """Return a compact dictionary summary for demos and smoke tests."""

        return {
            "time": self.time,
            "node_count": self.snapshot.node_count,
            "available_edge_count": self.available_edge_count,
            "total_edge_count": self.total_edge_count,
            "edge_attribute_count": len(self.edge_attributes),
        }

    @property
    def edge_attributes_tuple(self) -> Tuple[EdgeAttributes, ...]:
        """Return edge attributes as an immutable tuple."""

        return tuple(self.edge_attributes)
