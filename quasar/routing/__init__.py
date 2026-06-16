"""Routing interfaces and reference workloads for QUASAR."""

from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.dsp import OOSDSPRouter
from quasar.routing.easr import OOSEASRRouter
from quasar.routing.mpr import OOSMPRRouter
from quasar.routing.sd import SDRouter

__all__ = [
    "EntanglementRequest",
    "OOSDSPRouter",
    "OOSEASRRouter",
    "OOSMPRRouter",
    "RouteResult",
    "Router",
    "SDRouter",
]
