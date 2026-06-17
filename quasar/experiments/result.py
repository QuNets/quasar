"""Experiment result container for QUASAR smoke experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable


@dataclass(frozen=True)
class ExperimentResult:
    """Container returned by the paper-aligned experiment runner."""

    config: Any
    frames: Iterable[Any] = field(default_factory=tuple)
    snapshots: Iterable[Any] = field(default_factory=tuple)
    route_results: Iterable[Any] = field(default_factory=tuple)
    event_log: Any = None
    edge_trace: Any = None
    path_trace: Any = None
    summary: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", tuple(self.frames))
        object.__setattr__(self, "snapshots", tuple(self.snapshots))
        object.__setattr__(self, "route_results", tuple(self.route_results))

    def summary_dict(self) -> dict:
        """Return the metric summary as a dictionary."""

        if self.summary is None:
            return {}
        return self.summary.to_dict()

    def to_dict(self) -> dict:
        """Return a compact experiment result dictionary."""

        return {
            "architecture": self.config.architecture,
            "routing_algorithm": self.config.routing_algorithm,
            "time_points": tuple(self.config.time_points),
            "frame_count": len(self.frames),
            "snapshot_count": len(self.snapshots),
            "route_attempts": len(self.route_results),
            "route_successes": sum(1 for result in self.route_results if result.success),
            "summary": self.summary_dict(),
            "metadata": dict(self.metadata),
        }
