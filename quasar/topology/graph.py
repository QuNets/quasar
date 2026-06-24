"""Graph snapshot models for the QUASAR topology stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from quasar.satellite.models import LinkState


@dataclass(frozen=True)
class TopologySnapshot:
    """A dynamic graph snapshot G(t) exposed by the topology engine.

    ``edges`` contains candidate links after pruning rules have been applied to
    their availability flags. ``available_edges`` is the active edge set E_t
    used by later channel, architecture, and routing stages.
    """

    time: float
    nodes: Iterable[str] = field(default_factory=tuple)
    edges: Iterable[LinkState] = field(default_factory=tuple)
    available_edges: Iterable[LinkState] = field(init=False)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")

        nodes = tuple(self.nodes)
        edges = tuple(self.edges)
        if len(set(nodes)) != len(nodes):
            raise ValueError("nodes must be unique")
        for idx, node in enumerate(nodes):
            if not node:
                raise ValueError(f"nodes[{idx}] must be a non-empty string")

        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(
            self,
            "available_edges",
            tuple(edge for edge in edges if edge.available),
        )

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the snapshot."""

        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Return the number of available edges in G(t)."""

        return len(self.available_edges)
