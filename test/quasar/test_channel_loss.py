"""Tests for QUASAR channel loss helpers."""

from quasar.channel.loss import atmospheric_transmittance, total_transmittance
from quasar.channel.models import EdgeType


def test_lower_elevation_has_lower_atmospheric_transmittance():
    low = atmospheric_transmittance(elevation_deg=15.0, alpha=0.15, h0_km=20.0)
    high = atmospheric_transmittance(elevation_deg=60.0, alpha=0.15, h0_km=20.0)

    assert low < high


def test_sgl_total_transmittance_includes_atmospheric_penalty():
    eta0 = 0.5
    kappa = 0.8
    atmospheric = atmospheric_transmittance(elevation_deg=45.0, alpha=0.1, h0_km=10.0)

    total = total_transmittance(
        EdgeType.SGL,
        eta0=eta0,
        kappa=kappa,
        elevation_deg=45.0,
        alpha=0.1,
        h0_km=10.0,
    )

    assert total == eta0 * atmospheric * kappa


def test_isl_total_transmittance_ignores_atmospheric_penalty():
    total = total_transmittance(
        EdgeType.ISL,
        eta0=0.5,
        kappa=0.8,
        elevation_deg=5.0,
        alpha=10.0,
        h0_km=100.0,
    )

    assert total == 0.4
