"""Base scenario interfaces for QUASAR candidate link sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Protocol, Tuple

from quasar.satellite.models import GroundStation, LinkState, Satellite


@dataclass(frozen=True)
class ScenarioFrame:
    """A time-indexed set of nodes and candidate links."""

    time: float
    satellites: Iterable[Satellite] = field(default_factory=tuple)
    ground_stations: Iterable[GroundStation] = field(default_factory=tuple)
    candidate_links: Iterable[LinkState] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")
        satellites = tuple(self.satellites)
        ground_stations = tuple(self.ground_stations)
        candidate_links = tuple(self.candidate_links)
        node_names = tuple(node.name for node in satellites + ground_stations)
        if len(set(node_names)) != len(node_names):
            raise ValueError("satellites and ground stations must be unique")
        object.__setattr__(self, "satellites", satellites)
        object.__setattr__(self, "ground_stations", ground_stations)
        object.__setattr__(self, "candidate_links", candidate_links)


class CandidateLinkSource(Protocol):
    """Protocol for interchangeable time-indexed link sources."""

    def frame_at(self, time: float) -> ScenarioFrame:
        """Return a scenario frame for a simulation time."""
        ...

    def candidate_links_at(self, time: float) -> Tuple[LinkState, ...]:
        """Return candidate links for a simulation time."""

        return self.frame_at(time).candidate_links
