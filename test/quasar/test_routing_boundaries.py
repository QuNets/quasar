"""Boundary tests for Stage 6A routing scope."""

from pathlib import Path


def _routing_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("quasar/routing").glob("*.py")
    )


def test_routing_does_not_implement_events_or_run_loop():
    source = _routing_source()

    assert "EventBridge" not in source
    assert "GRAPH_UPDATE" not in source
    assert "LINK_DROP" not in source
    assert "FIDELITY_LOSS" not in source
    assert "ROUTE_RECOMPUTE" not in source
    assert "def run(" not in source
    assert "100 ms" not in source


def test_easr_objective_and_edge_weight_are_not_implemented_yet():
    source = _routing_source()

    assert not Path("quasar/routing/easr.py").exists()
    assert "omega_uv" not in source
    assert "DeltaTau" not in source
    assert "zeta_swap" not in source
    assert "xi *" not in source
