"""Minimal spatiotemporal satellite data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class Satellite:
    """A satellite node in a QUASAR constellation."""

    name: str
    altitude_km: Optional[float] = None
    inclination_deg: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundStation:
    """A fixed ground station represented by geodetic coordinates."""

    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_km: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisibilityWindow:
    """A time interval during which a satellite-ground link is visible."""

    satellite: str
    ground_station: str
    start_time: float
    end_time: float
    min_elevation_deg: Optional[float] = None


@dataclass
class LinkState:
    """Dynamic state for a candidate satellite-network link."""

    endpoints: Tuple[str, str]
    available: bool
    edge_type: Optional[str] = None
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    updated_at: Optional[float] = None
