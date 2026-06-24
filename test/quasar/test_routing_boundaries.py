"""Boundary tests for routing scope."""

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


def test_easr_remains_oos_only_and_separate_from_sd():
    source = Path("quasar/routing/easr.py").read_text(encoding="utf-8")

    assert Path("quasar/routing/easr.py").exists()
    assert "SimultaneousDownlinkArchitecture" not in source
    assert "find_simultaneous_downlink_opportunities" not in source
