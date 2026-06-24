"""Event log helpers for QUASAR metric collection."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

from quasar.events.record import EventRecord
from quasar.events.types import EventType


@dataclass
class EventLog:
    """Append-only log of QUASAR event records."""

    events: list = field(default_factory=list)

    def record(self, event: EventRecord) -> None:
        """Record one QUASAR event."""

        if not isinstance(event, EventRecord):
            raise TypeError("event must be an EventRecord")
        self.events.append(event)

    def extend(self, events: Iterable[EventRecord]) -> None:
        """Record multiple QUASAR events."""

        for event in events:
            self.record(event)

    def count_by_type(self) -> Dict[EventType, int]:
        """Return event counts grouped by event type."""

        return dict(Counter(event.event_type for event in self.events))

    @property
    def total_count(self) -> int:
        """Return the total number of recorded events."""

        return len(self.events)

    def to_records(self) -> Tuple[EventRecord, ...]:
        """Return recorded events as an immutable tuple."""

        return tuple(self.events)

    def summary(self) -> dict:
        """Return a compact event-log summary."""

        counts = self.count_by_type()
        return {
            "total_events": self.total_count,
            "event_counts": {
                event_type.value: count
                for event_type, count in counts.items()
            },
        }
