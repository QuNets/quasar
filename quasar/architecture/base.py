"""Base contracts for QUASAR hardware architecture models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Sequence


class ArchitectureMode(str, Enum):
    """Supported satellite hardware abstraction modes."""

    SIMULTANEOUS_DOWNLINK = "simultaneous_downlink"
    ON_ORBIT_STITCHING = "on_orbit_stitching"


def _validate_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass
class ArchitectureResult:
    """A hardware-architecture feasibility result."""

    feasible: bool
    architecture: ArchitectureMode
    storage_delay: float = 0.0
    fidelity: Optional[float] = None
    success_probability: Optional[float] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")
        _validate_probability(self.fidelity, "fidelity")
        _validate_probability(self.success_probability, "success_probability")


class BaseArchitecture(ABC):
    """Abstract hardware architecture model."""

    name = "architecture"
    mode: ArchitectureMode

    @abstractmethod
    def find_opportunities(self, graph: Any, request: Any, time: float = 0.0) -> Sequence[ArchitectureResult]:
        """Return feasible distribution opportunities at the given time."""
        raise NotImplementedError


Architecture = BaseArchitecture
