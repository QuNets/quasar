"""Small fixed-pair workload helpers for QUASAR experiments."""

from __future__ import annotations

from dataclasses import dataclass

from quasar.routing import EntanglementRequest
from quasar.satellite.models import GroundStation


@dataclass(frozen=True)
class FixedPairWorkload:
    """Generate requests for one controlled ground-station pair."""

    source: GroundStation
    destination: GroundStation

    def request_at(self, time: float) -> EntanglementRequest:
        """Return a request from source to destination at a time."""

        if time < 0:
            raise ValueError("time must be non-negative")
        return EntanglementRequest(
            source=self.source.name,
            destination=self.destination.name,
            created_at=time,
        )
