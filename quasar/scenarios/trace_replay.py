"""Trace replay scenario source for user-provided candidate links."""

from __future__ import annotations

from typing import Iterable, Mapping, Optional, Tuple

from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.scenarios.base import ScenarioFrame


class TraceReplaySource:
    """Replay user-provided scenario frames through the common source API."""

    def __init__(
        self,
        frames: Optional[Mapping[float, ScenarioFrame]] = None,
        candidate_links_by_time: Optional[Mapping[float, Iterable[LinkState]]] = None,
        satellites: Iterable[Satellite] = (),
        ground_stations: Iterable[GroundStation] = (),
        mode: str = "exact",
    ) -> None:
        if mode not in ("exact", "previous"):
            raise ValueError("mode must be 'exact' or 'previous'")
        self.mode = mode
        self._frames = {}
        if frames is not None:
            self._frames.update({float(time): frame for time, frame in frames.items()})
        if candidate_links_by_time is not None:
            satellites_tuple = tuple(satellites)
            ground_stations_tuple = tuple(ground_stations)
            for time, candidate_links in candidate_links_by_time.items():
                self._frames[float(time)] = ScenarioFrame(
                    time=float(time),
                    satellites=satellites_tuple,
                    ground_stations=ground_stations_tuple,
                    candidate_links=tuple(candidate_links),
                    metadata={"source": "trace_replay"},
                )
        if not self._frames:
            raise ValueError("TraceReplaySource requires at least one frame")

    def frame_at(self, time: float) -> ScenarioFrame:
        """Return a replayed scenario frame."""

        if time < 0:
            raise ValueError("time must be non-negative")
        key = float(time)
        if key in self._frames:
            return self._frames[key]
        if self.mode == "previous":
            previous_times = [frame_time for frame_time in self._frames if frame_time <= key]
            if previous_times:
                return self._frames[max(previous_times)]
        raise KeyError(f"no trace frame available at time {time}")

    def candidate_links_at(self, time: float) -> Tuple[LinkState, ...]:
        """Return replayed candidate links for a simulation time."""

        return self.frame_at(time).candidate_links
