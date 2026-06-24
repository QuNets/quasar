"""QUASAR-native event bridge for threshold-crossing detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from quasar.events.detector import ThresholdCrossingDetector
from quasar.events.record import EventRecord
from quasar.events.types import EventType


@dataclass
class EventBridge:
    """Collect event records emitted by QUASAR state-crossing checks."""

    detector: ThresholdCrossingDetector = field(default_factory=ThresholdCrossingDetector)
    events: List[EventRecord] = field(default_factory=list)

    def detect_events(
        self,
        previous_state: Any,
        current_state: Any,
        current_route: Any = None,
        thresholds: Any = None,
    ) -> List[EventRecord]:
        """Detect threshold crossings between two state snapshots."""

        records = self.detector.detect(
            previous_state=previous_state,
            current_state=current_state,
            current_route=current_route,
            thresholds=thresholds,
        )
        self.events.extend(records)
        return records

    def check_thresholds(self, edge_state: Any) -> List[EventRecord]:
        """Keep the early placeholder API as a no-op single-state check."""

        return []

    def trigger(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """Record an event emitted by the QUASAR overlay."""

        self.events.append(
            EventRecord(
                event_type=event_type,
                time=payload.get("time", 0.0),
                endpoints=payload.get("endpoints"),
                reason=payload.get("reason"),
                metadata=dict(payload),
            )
        )
