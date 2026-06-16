"""Routing interfaces and reference workloads for QUASAR."""

from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.dsp import OOSDSPRouter
from quasar.routing.mpr import OOSMPRRouter
from quasar.routing.sd import SDRouter

__all__ = [
    "EntanglementRequest",
    "OOSDSPRouter",
    "OOSMPRRouter",
    "RouteResult",
    "Router",
    "SDRouter",
]
