"""Success-probability helpers for QUASAR channel abstractions."""

from __future__ import annotations

from typing import Iterable, Optional


def _validate_probability(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


def path_success_probability(
    edge_transmittances: Iterable[float],
    swap_success_probabilities: Optional[Iterable[float]] = None,
) -> float:
    """Return path success probability as a product of edge and swap terms."""

    probability = 1.0
    for transmittance in edge_transmittances:
        _validate_probability(transmittance, "edge transmittance")
        probability *= transmittance

    if swap_success_probabilities is None:
        return probability

    for swap_probability in swap_success_probabilities:
        _validate_probability(swap_probability, "swap success probability")
        probability *= swap_probability

    return probability
