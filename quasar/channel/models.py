"""Minimal channel data models for dynamic QUASAR edges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EdgeType(str, Enum):
    """Supported satellite-network edge categories."""

    SGL = "SGL"
    ISL = "ISL"


@dataclass
class EdgeAttributes:
    """Network-layer attributes derived from physical link state."""

    edge_type: EdgeType
    available: bool = True
    transmittance: float = 1.0
    success_probability: Optional[float] = None
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    storage_delay: Optional[float] = None
    fidelity: Optional[float] = None
    routing_weight: Optional[float] = None

