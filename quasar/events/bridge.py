"""Placeholder event bridge for physical-to-network updates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from quasar.events.types import EventType


@dataclass
class EventBridge:
    """Collects QUASAR events until a SimQN adapter is added."""

    events: List[Tuple[EventType, Dict[str, Any]]] = field(default_factory=list)

    def check_thresholds(self, edge_state: Any) -> List[Tuple[EventType, Dict[str, Any]]]:
        """Inspect edge state and return newly triggered events.

        Stage 1 keeps this as a placeholder; threshold logic will be added after
        the dynamic link-state models are connected to SimQN events.
        """

        return []

    def trigger(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """Record an event emitted by the QUASAR overlay."""

        self.events.append((event_type, payload))

