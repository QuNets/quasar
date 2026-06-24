"""Channel data models for dynamic QUASAR edges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class EdgeType(str, Enum):
    """Supported satellite-network edge categories."""

    SGL = "SGL"
    ISL = "ISL"


def _validate_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass
class ChannelParameters:
    """Configurable constants for simplified optical-channel attributes."""

    base_transmittance: float = 1.0
    implementation_efficiency: float = 1.0
    atmospheric_attenuation: float = 0.0
    atmosphere_thickness_km: float = 0.0
    min_elevation_deg: float = 0.0

    def __post_init__(self) -> None:
        _validate_probability(self.base_transmittance, "base_transmittance")
        _validate_probability(self.implementation_efficiency, "implementation_efficiency")
        if self.atmospheric_attenuation < 0:
            raise ValueError("atmospheric_attenuation must be non-negative")
        if self.atmosphere_thickness_km < 0:
            raise ValueError("atmosphere_thickness_km must be non-negative")
        if not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")


@dataclass
class EdgeAttributes:
    """Network-layer attributes derived from physical link state."""

    edge_type: EdgeType
    endpoints: Optional[Tuple[str, str]] = None
    available: bool = True
    transmittance: float = 1.0
    success_probability: Optional[float] = None
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    storage_delay: Optional[float] = None
    fidelity: Optional[float] = None
    routing_weight: Optional[float] = None
    updated_at: Optional[float] = None

    def __post_init__(self) -> None:
        if self.endpoints is not None:
            if len(self.endpoints) != 2:
                raise ValueError("endpoints must contain exactly two node names")
            if not self.endpoints[0] or not self.endpoints[1]:
                raise ValueError("endpoints must contain non-empty node names")
        _validate_probability(self.transmittance, "transmittance")
        _validate_probability(self.success_probability, "success_probability")
        _validate_probability(self.fidelity, "fidelity")
        if self.distance_km is not None and self.distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if self.elevation_deg is not None and not -90.0 <= self.elevation_deg <= 90.0:
            raise ValueError("elevation_deg must be in [-90, 90]")
        if self.storage_delay is not None and self.storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")

    @property
    def effective_success_probability(self) -> float:
        """Return explicit success probability or fall back to transmittance."""

        if self.success_probability is not None:
            return self.success_probability
        return self.transmittance
