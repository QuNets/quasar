"""QUASAR event type definitions."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Discrete events emitted by the QUASAR physical-to-network bridge."""

    LINK_UP = "LINK_UP"
    LINK_DROP = "LINK_DROP"
    CHANNEL_DEGRADATION = "CHANNEL_DEGRADATION"
    CHANNEL_RECOVERY = "CHANNEL_RECOVERY"
    FIDELITY_LOSS = "FIDELITY_LOSS"
    FIDELITY_RECOVERY = "FIDELITY_RECOVERY"
    GRAPH_UPDATE = "GRAPH_UPDATE"
    ROUTE_RECOMPUTE = "ROUTE_RECOMPUTE"
    CHANNEL_UPDATE = "CHANNEL_UPDATE"
    REQUEST_ARRIVAL = "REQUEST_ARRIVAL"
    REQUEST_SUCCESS = "REQUEST_SUCCESS"
    REQUEST_FAILURE = "REQUEST_FAILURE"
