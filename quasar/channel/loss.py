"""Lightweight optical-loss helpers for QUASAR channel attributes."""

from __future__ import annotations

import math
from typing import Optional, Union

from quasar.channel.models import EdgeType


def _validate_probability(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


def atmospheric_transmittance(elevation_deg: float, alpha: float, h0_km: float) -> float:
    """Return the elevation-dependent atmospheric transmittance penalty.

    This implements the manuscript's cosecant-law approximation:
    eta_alpha(theta) = exp(-alpha * h0 / sin(theta)).
    """

    if not 0.0 <= elevation_deg <= 90.0:
        raise ValueError("elevation_deg must be in [0, 90]")
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    if h0_km < 0:
        raise ValueError("h0_km must be non-negative")
    if elevation_deg == 0.0:
        return 0.0

    sin_theta = math.sin(math.radians(elevation_deg))
    return math.exp(-(alpha * h0_km) / sin_theta)


def total_transmittance(
    edge_type: Union[EdgeType, str],
    eta0: float,
    kappa: float,
    elevation_deg: Optional[float] = None,
    alpha: Optional[float] = None,
    h0_km: Optional[float] = None,
) -> float:
    """Return total edge transmittance for an SGL or ISL edge.

    ISL: eta = eta0 * kappa.
    SGL: eta = eta0 * eta_alpha(theta) * kappa.
    """

    _validate_probability(eta0, "eta0")
    _validate_probability(kappa, "kappa")

    edge = EdgeType(edge_type)
    if edge == EdgeType.ISL:
        return eta0 * kappa

    if elevation_deg is None:
        raise ValueError("elevation_deg is required for SGL transmittance")
    if alpha is None:
        raise ValueError("alpha is required for SGL transmittance")
    if h0_km is None:
        raise ValueError("h0_km is required for SGL transmittance")

    return eta0 * atmospheric_transmittance(elevation_deg, alpha, h0_km) * kappa
