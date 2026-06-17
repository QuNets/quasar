"""Storage-delay estimates from sampled QUASAR contact schedules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from quasar.timing.contact_schedule import ContactSchedule


@dataclass(frozen=True)
class StorageDelayEstimator:
    """Estimate OOS storage delay from sampled contact windows.

    Estimates are sampled contact-window-derived delays. They are not full
    entanglement scheduling, resource reservation, or queueing.
    """

    schedule: ContactSchedule
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        metadata = {
            "storage_delay_source": "sampled_contact_schedule_estimator",
            "storage_delay_policy": "contact_window_age",
            "not_resource_reservation": True,
            **self.metadata,
        }
        object.__setattr__(self, "metadata", metadata)

    def estimate_edge_delay(
        self,
        edge: Any,
        current_time: float,
        mode: str = "next_contact_gap",
    ) -> Optional[float]:
        """Return a non-negative sampled contact delay estimate."""

        if mode not in ("next_contact_gap", "contact_window_age"):
            raise ValueError("unsupported edge delay mode")
        if current_time < 0:
            raise ValueError("current_time must be non-negative")
        if mode == "contact_window_age":
            active_window = self.schedule.active_window(edge, current_time)
            if active_window is not None:
                return max(0.0, current_time - active_window.start_time)

        next_time = self.schedule.next_contact_time(edge, current_time)
        if next_time is None:
            return None
        return max(0.0, next_time - current_time)

    def estimate_path_delay(
        self,
        path: Any,
        current_time: float,
        mode: str = "sum",
    ) -> Optional[float]:
        """Return the sum of sampled edge delays for a path."""

        if mode != "sum":
            raise ValueError("unsupported path delay mode")
        total = 0.0
        for edge in _path_edges(path):
            delay = self.estimate_edge_delay(edge, current_time)
            if delay is None:
                return None
            total += delay
        return total


def _path_edges(path: Any) -> Tuple[Any, ...]:
    if hasattr(path, "path"):
        path = path.path
    items = tuple(path)
    if not items:
        return ()
    if all(hasattr(item, "endpoints") for item in items):
        return items
    if all(isinstance(item, str) for item in items):
        if len(items) < 2:
            return ()
        return tuple(zip(items, items[1:]))
    return tuple(_validate_endpoint_pair(item) for item in items)


def _validate_endpoint_pair(item: Any) -> Tuple[str, str]:
    pair = tuple(item)
    if len(pair) != 2:
        raise ValueError("path items must be edges or endpoint pairs")
    first, second = pair
    if not first or not second:
        raise ValueError("path endpoint pairs must be non-empty")
    return first, second
