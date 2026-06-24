"""Event record models for QUASAR-native threshold crossings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from quasar.events.types import EventType


@dataclass(frozen=True)
class EventRecord:
    """A single physical-to-network event detected by QUASAR."""

    event_type: EventType
    time: float = 0.0
    endpoints: Optional[Tuple[str, str]] = None
    previous_value: Any = None
    current_value: Any = None
    threshold: Optional[float] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")
        if self.endpoints is not None:
            if len(self.endpoints) != 2:
                raise ValueError("endpoints must contain exactly two nodes")
            first, second = self.endpoints
            if not first or not second:
                raise ValueError("endpoints must contain non-empty nodes")
            object.__setattr__(self, "endpoints", (first, second))
        if self.threshold is not None and not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
