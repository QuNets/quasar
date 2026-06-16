"""Minimal deterministic QUASAR single-step demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.api import QuasarSimulator
from quasar.channel.models import ChannelParameters, EdgeType
from quasar.satellite.models import LinkState


def _format_float(value, digits=4, suffix=""):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}"


def _print_step_result(result):
    print("# QUASAR basic demo")
    print()
    print(f"Time: {result.time:.3f} s")
    print(f"Nodes: {result.snapshot.node_count}")
    print(f"Available edges: {result.available_edge_count} / {result.total_edge_count}")
    print(f"Attributed edges: {len(result.edge_attributes)}")
    print()
    print("Available edge attributes:")

    for index, attributes in enumerate(result.edge_attributes, start=1):
        edge_type = attributes.edge_type.value
        source, destination = attributes.endpoints
        print(f"[{index}] {edge_type} {source} -> {destination}")
        print(f"distance:      {_format_float(attributes.distance_km, digits=3, suffix=' km')}")
        print(f"elevation:     {_format_float(attributes.elevation_deg, digits=3, suffix=' deg')}")
        print(f"transmittance: {_format_float(attributes.transmittance)}")
        print(f"success prob.: {_format_float(attributes.success_probability)}")
        print(f"storage delay: {_format_float(attributes.storage_delay, suffix=' s')}")
        print(f"fidelity:      {_format_float(attributes.fidelity)}")
        print()


def main() -> None:
    simulator = QuasarSimulator(
        min_elevation_deg=15.0,
        max_sgl_range_km=1200.0,
        max_isl_range_km=2000.0,
        channel_parameters=ChannelParameters(
            base_transmittance=0.5,
            implementation_efficiency=0.85,
            atmospheric_attenuation=0.02,
            atmosphere_thickness_km=10.0,
        ),
        default_storage_delay=0.01,
    )
    simulator.add_satellite("SAT-1", altitude_km=500.0, inclination_deg=53.0)
    simulator.add_satellite("SAT-2", altitude_km=500.0, inclination_deg=53.0)
    simulator.add_ground_station("GS-PEK", latitude_deg=39.9, longitude_deg=116.4)

    candidate_links = [
        LinkState(
            endpoints=("SAT-1", "GS-PEK"),
            edge_type=EdgeType.SGL,
            distance_km=700.0,
            elevation_deg=35.0,
        ),
        LinkState(
            endpoints=("SAT-2", "GS-PEK"),
            edge_type=EdgeType.SGL,
            distance_km=900.0,
            elevation_deg=8.0,
        ),
        LinkState(
            endpoints=("SAT-1", "SAT-2"),
            edge_type=EdgeType.ISL,
            distance_km=1500.0,
        ),
    ]

    result = simulator.step(time=0.0, candidate_links=candidate_links)
    _print_step_result(result)


if __name__ == "__main__":
    main()
