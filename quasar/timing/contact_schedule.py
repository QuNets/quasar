"""Sampled contact schedules derived from explicit topology snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple

from quasar.timing.contact_window import ContactWindow, canonical_edge_key
from quasar.topology.engine import SpatiotemporalTopologyEngine


@dataclass(frozen=True)
class ContactSchedule:
    """Contact windows sampled from explicit times and topology snapshots."""

    windows: Mapping[Tuple[str, str], Iterable[ContactWindow]] = field(
        default_factory=dict
    )
    time_points: Iterable[float] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = {
            canonical_edge_key(key): tuple(value)
            for key, value in self.windows.items()
        }
        time_points = tuple(self.time_points)
        if any(time < 0 for time in time_points):
            raise ValueError("time_points must be non-negative")
        if tuple(sorted(time_points)) != time_points:
            raise ValueError("time_points must be sorted")
        object.__setattr__(self, "windows", normalized)
        object.__setattr__(self, "time_points", time_points)

    @classmethod
    def from_source(
        cls,
        source: Any,
        time_points: Iterable[float],
        topology_engine_factory: Optional[Callable[[Any], Any]] = None,
        min_elevation_deg: float = 15.0,
        max_sgl_range_km: Optional[float] = None,
        max_isl_range_km: Optional[float] = None,
    ) -> "ContactSchedule":
        """Build a sampled contact schedule from a link source and time grid."""

        times = tuple(time_points)
        _validate_time_points(times)
        samples_by_time = []
        snapshots = []
        for time in times:
            frame = source.frame_at(time)
            engine = _topology_engine(
                frame,
                topology_engine_factory,
                min_elevation_deg,
                max_sgl_range_km,
                max_isl_range_km,
            )
            snapshot = engine.build_snapshot(time, frame.candidate_links)
            snapshots.append(snapshot)
            samples_by_time.append((time, tuple(snapshot.available_edges)))

        return cls(
            windows=_build_windows(samples_by_time),
            time_points=times,
            metadata={
                "source": "sampled_contact_schedule",
                "sample_count": len(times),
                "snapshot_count": len(snapshots),
            },
        )

    def windows_for(self, edge: Any) -> Tuple[ContactWindow, ...]:
        """Return sampled windows for an edge or endpoint pair."""

        return tuple(self.windows.get(canonical_edge_key(edge), ()))

    def active_window(self, edge: Any, time: float) -> Optional[ContactWindow]:
        """Return the sampled window containing time, if one exists."""

        for window in self.windows_for(edge):
            if window.contains(time):
                return window
        return None

    def next_contact_time(self, edge: Any, current_time: float) -> Optional[float]:
        """Return current_time, a future start time, or None if no contact exists."""

        if current_time < 0:
            raise ValueError("current_time must be non-negative")
        if self.active_window(edge, current_time) is not None:
            return current_time
        for window in self.windows_for(edge):
            if window.start_time >= current_time:
                return window.start_time
        return None


def _topology_engine(
    frame: Any,
    topology_engine_factory: Optional[Callable[[Any], Any]],
    min_elevation_deg: float,
    max_sgl_range_km: Optional[float],
    max_isl_range_km: Optional[float],
) -> Any:
    if topology_engine_factory is not None:
        return topology_engine_factory(frame)
    return SpatiotemporalTopologyEngine(
        satellites=frame.satellites,
        ground_stations=frame.ground_stations,
        min_elevation_deg=min_elevation_deg,
        max_sgl_range_km=max_sgl_range_km,
        max_isl_range_km=max_isl_range_km,
    )


def _build_windows(
    samples_by_time: Iterable[Tuple[float, Iterable[Any]]],
) -> Dict[Tuple[str, str], Tuple[ContactWindow, ...]]:
    active = {}
    windows = {}
    for time, edges in samples_by_time:
        available = {canonical_edge_key(edge): edge for edge in edges}
        for key in tuple(active):
            if key not in available:
                _close_window(windows, key, active.pop(key))
        for key, edge in available.items():
            if key in active:
                active[key]["sample_times"].append(time)
                active[key]["end_time"] = time
            else:
                active[key] = {
                    "edge_type": edge.edge_type,
                    "start_time": time,
                    "end_time": time,
                    "sample_times": [time],
                }
    for key, data in active.items():
        _close_window(windows, key, data)
    return {key: tuple(value) for key, value in windows.items()}


def _close_window(windows: Dict, key: Tuple[str, str], data: Dict[str, Any]) -> None:
    windows.setdefault(key, []).append(
        ContactWindow(
            endpoints=key,
            edge_type=data["edge_type"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            sample_times=tuple(data["sample_times"]),
            metadata={
                "source": "sampled_contact_schedule",
                "sampled": True,
            },
        )
    )


def _validate_time_points(time_points: Tuple[float, ...]) -> None:
    if not time_points:
        raise ValueError("time_points must not be empty")
    if any(time < 0 for time in time_points):
        raise ValueError("time_points must be non-negative")
    if tuple(sorted(time_points)) != time_points:
        raise ValueError("time_points must be sorted")
