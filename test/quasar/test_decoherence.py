"""Tests for QUASAR memory decoherence helpers."""

from quasar.memory.decoherence import fidelity_after_storage, is_fidelity_feasible


def test_storage_delay_reduces_fidelity():
    short_delay = fidelity_after_storage(delta_tau=0.01, f0=0.99, tau_c=0.1)
    long_delay = fidelity_after_storage(delta_tau=0.2, f0=0.99, tau_c=0.1)

    assert long_delay < short_delay


def test_fidelity_threshold_feasibility():
    assert is_fidelity_feasible(0.9, 0.75)
    assert not is_fidelity_feasible(0.7, 0.75)
