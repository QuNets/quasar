"""Base interface for QUASAR hardware architecture models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class Architecture(ABC):
    """Abstract hardware architecture model."""

    name = "architecture"

    @abstractmethod
    def find_opportunities(self, graph: Any, request: Any, time: float) -> Sequence[Any]:
        """Return feasible distribution opportunities at the given time."""
        raise NotImplementedError

