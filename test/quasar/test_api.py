"""Smoke tests for the user-facing QUASAR API."""

from quasar.api import QuasarSimulator, QuasarStepResult
from quasar.channel.models import ChannelParameters, EdgeType
from quasar.satellite.models import LinkState


def test_quasar_simulator_step_returns_result_with_edge_attributes():
    simulator = QuasarSimulator(
        min_elevation_deg=15.0,
        max_sgl_range_km=1000.0,
        channel_parameters=ChannelParameters(
            base_transmittance=0.5,
            implementation_efficiency=0.8,
            atmospheric_attenuation=0.02,
            atmosphere_thickness_km=10.0,
        ),
        default_storage_delay=0.01,
    )
    simulator.add_satellite("sat-1")
    simulator.add_ground_station("gs-1", latitude_deg=30.0, longitude_deg=120.0)
    candidate_links = [
        LinkState(
            endpoints=("sat-1", "gs-1"),
            edge_type=EdgeType.SGL,
            distance_km=600.0,
            elevation_deg=30.0,
        ),
        LinkState(
            endpoints=("sat-1", "gs-1"),
            edge_type=EdgeType.SGL,
            distance_km=600.0,
            elevation_deg=5.0,
        ),
    ]

    result = simulator.step(time=1.0, candidate_links=candidate_links)

    assert isinstance(result, QuasarStepResult)
    assert result.available_edge_count == 1
    assert result.total_edge_count == 2
    assert len(result.edge_attributes) == 1

    attributes = result.edge_attributes[0]
    assert attributes.transmittance < 0.5 * 0.8
    assert attributes.success_probability == attributes.transmittance
    assert attributes.fidelity is not None
    assert attributes.storage_delay == 0.01
