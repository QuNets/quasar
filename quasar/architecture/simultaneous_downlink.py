"""Simultaneous Downlink hardware abstraction."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from quasar.architecture.base import ArchitectureMode, ArchitectureResult, BaseArchitecture
from quasar.channel.models import EdgeType
from quasar.channel.probability import path_success_probability
from quasar.satellite.models import LinkState
from quasar.topology.graph import TopologySnapshot


class SimultaneousDownlinkArchitecture(BaseArchitecture):
    """Memoryless SD abstraction over simultaneous dual downlinks."""

    name = "simultaneous_downlink"
    mode = ArchitectureMode.SIMULTANEOUS_DOWNLINK

    def find_opportunities(
        self,
        graph: TopologySnapshot,
        request: Any,
        time: float = 0.0,
    ) -> List[ArchitectureResult]:
        """Return all same-satellite dual-downlink opportunities."""

        source, destination = _request_endpoints(request)
        return find_simultaneous_downlink_opportunities(graph, source, destination)


def find_simultaneous_downlink_opportunities(
    graph: TopologySnapshot,
    source_ground_station: str,
    destination_ground_station: str,
) -> List[ArchitectureResult]:
    """Return feasible SD opportunities for a ground-station pair.

    SD is memoryless: storage delay is zero, no memory decoherence is applied,
    and each result corresponds to one satellite that sees both ground stations
    in the same topology snapshot.
    """

    if source_ground_station == destination_ground_station:
        raise ValueError("ground stations must be distinct")

    source_edges = _sgl_edges_by_satellite(graph, source_ground_station)
    destination_edges = _sgl_edges_by_satellite(graph, destination_ground_station)
    opportunities = []

    for satellite in sorted(set(source_edges).intersection(destination_edges)):
        first_edge = source_edges[satellite]
        second_edge = destination_edges[satellite]
        transmittances = (_edge_transmittance(first_edge), _edge_transmittance(second_edge))
        success_probability = path_success_probability(transmittances)
        opportunities.append(
            ArchitectureResult(
                feasible=True,
                architecture=ArchitectureMode.SIMULTANEOUS_DOWNLINK,
                storage_delay=0.0,
                fidelity=None,
                success_probability=success_probability,
                reason=None,
                metadata={
                    "satellite": satellite,
                    "ground_stations": (source_ground_station, destination_ground_station),
                    "downlinks": (first_edge.endpoints, second_edge.endpoints),
                    "transmittances": transmittances,
                },
            )
        )

    return opportunities


def _request_endpoints(request: Any) -> Tuple[str, str]:
    if isinstance(request, dict):
        return request["source"], request["destination"]
    if isinstance(request, (tuple, list)) and len(request) == 2:
        return request[0], request[1]
    return request.source, request.destination


def _sgl_edges_by_satellite(graph: TopologySnapshot, ground_station: str) -> Dict[str, LinkState]:
    edges = {}
    for edge in graph.available_edges:
        satellite = _satellite_for_ground_station(edge, ground_station)
        if satellite is not None:
            edges[satellite] = edge
    return edges


def _satellite_for_ground_station(edge: LinkState, ground_station: str) -> str:
    if edge.edge_type != EdgeType.SGL or not edge.available:
        return None
    first, second = edge.endpoints
    if first == ground_station:
        return second
    if second == ground_station:
        return first
    return None


def _edge_transmittance(edge: LinkState) -> float:
    if edge.transmittance is None:
        return 1.0
    return edge.transmittance
