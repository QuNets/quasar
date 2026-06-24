"""Tests for QUASAR success-probability helpers."""

from quasar.channel.probability import path_success_probability


def test_path_success_probability_multiplies_edges_and_swaps():
    probability = path_success_probability(
        edge_transmittances=[0.5, 0.25],
        swap_success_probabilities=[0.8, 0.5],
    )

    assert probability == 0.5 * 0.25 * 0.8 * 0.5
