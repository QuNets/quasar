"""Lightweight quantum-memory decoherence helpers."""

from __future__ import annotations

import math


def fidelity_after_storage(delta_tau: float, f0: float, tau_c: float) -> float:
    """Return stored-pair fidelity after a storage duration.

    The model follows the QUASAR manuscript:
    F(delta_tau) = 1/4 + (F0 - 1/4) * exp(-delta_tau / tau_c).
    """

    if delta_tau < 0:
        raise ValueError("delta_tau must be non-negative")
    if tau_c <= 0:
        raise ValueError("tau_c must be positive")
    return 0.25 + (f0 - 0.25) * math.exp(-delta_tau / tau_c)
