"""QUASAR event type definitions."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Discrete events emitted by the QUASAR physical-to-network bridge."""

    LINK_UP = "LINK_UP"
    LINK_DROP = "LINK_DROP"
    CHANNEL_UPDATE = "CHANNEL_UPDATE"
    FIDELITY_LOSS = "FIDELITY_LOSS"
    ROUTE_RECOMPUTE = "ROUTE_RECOMPUTE"
    REQUEST_ARRIVAL = "REQUEST_ARRIVAL"
    REQUEST_SUCCESS = "REQUEST_SUCCESS"
    REQUEST_FAILURE = "REQUEST_FAILURE"
