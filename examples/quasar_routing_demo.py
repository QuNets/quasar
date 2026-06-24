"""Deterministic QUASAR routing-layer demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.channel.models import EdgeAttributes, EdgeType  # noqa: E402
from quasar.routing import (  # noqa: E402
    EntanglementRequest,
    OOSDSPRouter,
    OOSEASRRouter,
    OOSMPRRouter,
    SDRouter,
)
from quasar.satellite.models import LinkState  # noqa: E402
from quasar.topology.graph import TopologySnapshot  # noqa: E402


def _format_float(value, digits=4, suffix=""):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}"


def _format_path(path):
    if not path:
        return "n/a"
    return " -> ".join(path)


def _print_route_result(title, result):
    print(title)
    print(f"path:          {_format_path(result.path_tuple)}")
    print(f"success:       {result.success}")
    print(f"cost:          {_format_float(result.cost)}")
    print(f"success prob.: {_format_float(result.success_probability)}")
    print(f"storage delay: {_format_float(result.storage_delay, suffix=' s')}")
    print(f"fidelity:      {_format_float(result.fidelity)}")
    objective_score = result.metadata.get("objective_score")
    if objective_score is not None:
        print(f"EASR score:    {_format_float(objective_score)}")
    if result.reason:
        print(f"reason:        {result.reason}")
    print()


def _print_sd_result(result):
    print("SD selected opportunity")
    print(f"success:       {result.success}")
    print(f"cost:          {_format_float(result.cost)}")
    print(f"success prob.: {_format_float(result.success_probability)}")
    print(f"storage delay: {_format_float(result.storage_delay, suffix=' s')}")
    selected = result.metadata.get("selected_opportunity")
    if selected is not None:
        metadata = selected.metadata
        print(f"satellite:     {metadata['satellite']}")
        print(f"ground pair:   {_format_path(metadata['ground_stations'])}")
        print(f"transmittance: {_format_path(_format_float(v) for v in metadata['transmittances'])}")
    if result.reason:
        print(f"reason:        {result.reason}")
    print()


def _build_snapshot():
    nodes = (
        "GS-A",
        "GS-B",
        "SAT-SD-1",
        "SAT-SD-2",
        "SAT-DSP",
        "SAT-MPR-1",
        "SAT-MPR-2",
        "SAT-EASR-1",
        "SAT-EASR-2",
    )
    edges = (
        LinkState(("SAT-SD-1", "GS-A"), EdgeType.SGL, transmittance=0.42),
        LinkState(("SAT-SD-1", "GS-B"), EdgeType.SGL, transmittance=0.36),
        LinkState(("SAT-SD-2", "GS-A"), EdgeType.SGL, transmittance=0.60),
        LinkState(("SAT-SD-2", "GS-B"), EdgeType.SGL, transmittance=0.20),
        LinkState(("GS-A", "SAT-DSP"), EdgeType.SGL, transmittance=0.20),
        LinkState(("SAT-DSP", "GS-B"), EdgeType.SGL, transmittance=0.20),
        LinkState(("GS-A", "SAT-MPR-1"), EdgeType.SGL, transmittance=0.90),
        LinkState(("SAT-MPR-1", "SAT-MPR-2"), EdgeType.ISL, transmittance=0.90),
        LinkState(("SAT-MPR-2", "GS-B"), EdgeType.SGL, transmittance=0.90),
        LinkState(("GS-A", "SAT-EASR-1"), EdgeType.SGL, transmittance=0.72),
        LinkState(("SAT-EASR-1", "SAT-EASR-2"), EdgeType.ISL, transmittance=0.72),
        LinkState(("SAT-EASR-2", "GS-B"), EdgeType.SGL, transmittance=0.72),
    )
    return TopologySnapshot(time=0.0, nodes=nodes, edges=edges)


def _oos_edge_attributes():
    return (
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("GS-A", "SAT-DSP"),
            transmittance=0.20,
            storage_delay=0.00,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-DSP", "GS-B"),
            transmittance=0.20,
            storage_delay=0.00,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("GS-A", "SAT-MPR-1"),
            transmittance=0.90,
            storage_delay=0.18,
        ),
        EdgeAttributes(
            edge_type=EdgeType.ISL,
            endpoints=("SAT-MPR-1", "SAT-MPR-2"),
            transmittance=0.90,
            storage_delay=0.12,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-MPR-2", "GS-B"),
            transmittance=0.90,
            storage_delay=0.00,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("GS-A", "SAT-EASR-1"),
            transmittance=0.72,
            storage_delay=0.00,
        ),
        EdgeAttributes(
            edge_type=EdgeType.ISL,
            endpoints=("SAT-EASR-1", "SAT-EASR-2"),
            transmittance=0.72,
            storage_delay=0.03,
        ),
        EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-EASR-2", "GS-B"),
            transmittance=0.72,
            storage_delay=0.00,
        ),
    )


def main() -> None:
    snapshot = _build_snapshot()
    sd_request = EntanglementRequest("GS-A", "GS-B")
    oos_request = EntanglementRequest(
        "GS-A",
        "GS-B",
        metadata={
            "edge_attributes": _oos_edge_attributes(),
            "swap_success_probability": 1.0,
        },
    )

    sd_result = SDRouter().compute_route(snapshot, sd_request, time=0.0)
    dsp_result = OOSDSPRouter().compute_route(snapshot, oos_request, time=0.0)
    mpr_result = OOSMPRRouter().compute_route(snapshot, oos_request, time=0.0)
    easr_result = OOSEASRRouter(
        tau_c=0.10,
        xi=1.0,
        fidelity_threshold=0.75,
    ).compute_route(snapshot, oos_request, time=0.0)

    print("# QUASAR routing demo")
    print()
    print("Deterministic toy topology, time: 0.000 s")
    print("Storage delays below are synthetic demo-level values.")
    print("A later orbital/contact scheduler should provide real delays.")
    print()
    _print_sd_result(sd_result)
    _print_route_result("OOS DSP selected path", dsp_result)
    _print_route_result("OOS MPR selected path", mpr_result)
    _print_route_result("OOS EASR selected path", easr_result)


if __name__ == "__main__":
    main()
