"""Baseline controlled ground-station pairs for QUASAR experiments."""

from __future__ import annotations

from quasar.experiments.config import ControlledPairConfig
from quasar.satellite.models import GroundStation


def houston_washington_pair(
    config: ControlledPairConfig = ControlledPairConfig(),
) -> tuple:
    """Return the paper-aligned Houston to Washington-DC pair."""

    return (
        GroundStation(
            config.source_name,
            latitude_deg=config.source_latitude_deg,
            longitude_deg=config.source_longitude_deg,
        ),
        GroundStation(
            config.destination_name,
            latitude_deg=config.destination_latitude_deg,
            longitude_deg=config.destination_longitude_deg,
        ),
    )
