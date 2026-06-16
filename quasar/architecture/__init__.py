"""Hardware architecture interfaces for QUASAR."""

from quasar.architecture.base import Architecture, ArchitectureMode, ArchitectureResult, BaseArchitecture
from quasar.architecture.on_orbit_stitching import OnOrbitStitchingArchitecture
from quasar.architecture.simultaneous_downlink import (
    SimultaneousDownlinkArchitecture,
    find_simultaneous_downlink_opportunities,
)

__all__ = [
    "Architecture",
    "ArchitectureMode",
    "ArchitectureResult",
    "BaseArchitecture",
    "OnOrbitStitchingArchitecture",
    "SimultaneousDownlinkArchitecture",
    "find_simultaneous_downlink_opportunities",
]
