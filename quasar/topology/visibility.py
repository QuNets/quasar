"""Visibility and range pruning helpers for QUASAR topology snapshots."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from quasar.channel.models import EdgeType
from quasar.satellite.models import LinkState


def is_elevation_visible(elevation_deg: Optional[float], min_elevation_deg: float) -> bool:
    """Return whether an elevation angle satisfies the LOS mask."""

    if not 0.0 <= min_elevation_deg <= 90.0:
        raise ValueError("min_elevation_deg must be in [0, 90]")
    if elevation_deg is None:
        return False
    return elevation_deg >= min_elevation_deg


def is_range_feasible(distance_km: Optional[float], max_range_km: Optional[float]) -> bool:
    """Return whether a distance satisfies an optional range constraint."""

    if max_range_km is None:
        return True
    if max_range_km < 0:
        raise ValueError("max_range_km must be non-negative")
    if distance_km is None:
        return False
    return 0.0 <= distance_km <= max_range_km


def apply_visibility_mask(
    link_state: LinkState,
    min_elevation_deg: float = 15.0,
    max_range_km: Optional[float] = None,
) -> LinkState:
    """Return a link state after LOS and range pruning.

    SGL edges require an elevation angle that satisfies the minimum LOS mask.
    ISL edges do not use ground elevation in this minimal engine; their
    feasibility is represented by the input ``available`` flag and the optional
    range constraint.
    """

    elevation_ok = True
    if link_state.edge_type == EdgeType.SGL:
        elevation_ok = is_elevation_visible(link_state.elevation_deg, min_elevation_deg)

    range_ok = is_range_feasible(link_state.distance_km, max_range_km)
    return replace(link_state, available=link_state.available and elevation_ok and range_ok)
