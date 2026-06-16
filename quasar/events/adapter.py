"""Thin adapter from QUASAR event records to SimQN events."""

from __future__ import annotations

from typing import Callable, Optional

from qns.simulator import Event, Simulator, func_to_event

from quasar.events.record import EventRecord


class SimQNEventAdapter:
    """Wrap QUASAR event records as SimQN-compatible callbacks."""

    def to_callback(
        self,
        record: EventRecord,
        callback: Callable[[EventRecord], None],
    ) -> Callable[[], None]:
        """Return a callback wrapper that passes through the event record."""

        def wrapper() -> None:
            callback(record)

        return wrapper

    def to_event(
        self,
        record: EventRecord,
        callback: Callable[[EventRecord], None],
        simulator: Simulator,
        by: Optional[object] = None,
        name: Optional[str] = None,
    ) -> Event:
        """Wrap an event record callback as a SimQN event."""

        event_time = simulator.time(sec=record.time)
        event_name = name or f"QUASAR:{record.event_type.value}"
        return func_to_event(
            t=event_time,
            fn=self.to_callback(record, callback),
            name=event_name,
            by=by,
        )

    def schedule(
        self,
        simulator: Simulator,
        record: EventRecord,
        callback: Callable[[EventRecord], None],
        by: Optional[object] = None,
        name: Optional[str] = None,
    ) -> Event:
        """Create a SimQN event, add it to the simulator, and return it."""

        event = self.to_event(
            record=record,
            callback=callback,
            simulator=simulator,
            by=by,
            name=name,
        )
        simulator.add_event(event)
        return event
