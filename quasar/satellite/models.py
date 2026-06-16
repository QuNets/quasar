"""Spatiotemporal satellite data models used by the QUASAR overlay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from quasar.channel.models import EdgeType


def _require_name(name: str, field_name: str) -> None:
    if not name:
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass
class Satellite:
    """A satellite node in a QUASAR constellation.

    Stage 2 stores only descriptive orbit metadata. Real propagation is kept
    outside this model and can be added by later topology engines.
    """

    name: str
    altitude_km: Optional[float] = None
    inclination_deg: Optional[float] = None
    orbit_plane: Optional[int] = None
    slot: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_name(self.name, "name")
        if self.altitude_km is not None and self.altitude_km < 0:
            raise ValueError("altitude_km must be non-negative")
        if self.inclination_deg is not None and not 0.0 <= self.inclination_deg <= 180.0:
            raise ValueError("inclination_deg must be in [0, 180]")
        if self.orbit_plane is not None and self.orbit_plane < 0:
            raise ValueError("orbit_plane must be non-negative")
        if self.slot is not None and self.slot < 0:
            raise ValueError("slot must be non-negative")


@dataclass
class GroundStation:
    """A fixed ground station represented by geodetic coordinates."""

    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_km: float = 0.0
    min_elevation_deg: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_name(self.name, "name")
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude_deg must be in [-90, 90]")
        if not -180.0 <= self.longitude_deg <= 180.0:
            raise ValueError("longitude_deg must be in [-180, 180]")
        if not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")


@dataclass
class VisibilityWindow:
    """A time interval during which a satellite-ground link is visible."""

    satellite: str
    ground_station: str
    start_time: float
    end_time: float
    min_elevation_deg: Optional[float] = None
    max_elevation_deg: Optional[float] = None

    def __post_init__(self) -> None:
        _require_name(self.satellite, "satellite")
        _require_name(self.ground_station, "ground_station")
        if self.end_time < self.start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        if self.min_elevation_deg is not None and not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")
        if self.max_elevation_deg is not None and not 0.0 <= self.max_elevation_deg <= 90.0:
            raise ValueError("max_elevation_deg must be in [0, 90]")

    @property
    def duration(self) -> float:
        """Return the window duration in simulation seconds."""

        return self.end_time - self.start_time

    def contains(self, time: float) -> bool:
        """Return whether the given simulation time is inside the window."""

        return self.start_time <= time <= self.end_time


@dataclass
class LinkState:
    """Dynamic state for a candidate satellite-network link."""

    endpoints: Tuple[str, str]
    edge_type: EdgeType
    available: bool = True
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    transmittance: Optional[float] = None
    fidelity: Optional[float] = None
    updated_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.endpoints) != 2:
            raise ValueError("endpoints must contain exactly two node names")
        for idx, endpoint in enumerate(self.endpoints):
            _require_name(endpoint, f"endpoints[{idx}]")
        if self.endpoints[0] == self.endpoints[1]:
            raise ValueError("link endpoints must be distinct")
        if self.distance_km is not None and self.distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if self.elevation_deg is not None and not -90.0 <= self.elevation_deg <= 90.0:
            raise ValueError("elevation_deg must be in [-90, 90]")
        _validate_probability(self.transmittance, "transmittance")
        _validate_probability(self.fidelity, "fidelity")
