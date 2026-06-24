"""Max-Probability Routing baseline for OOS routing."""

from __future__ import annotations

from heapq import heappop, heappush
from math import isinf
from typing import Any, Dict, Iterable, List, Optional, Tuple

from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.utils import (
    path_transmittance_product,
    reconstruct_path,
    safe_negative_log,
)


class OOSMPRRouter(Router):
    """OOS-only baseline that maximizes path success probability."""

    name = "oos_mpr"

    def compute_route(
        self,
        graph,
        request: EntanglementRequest,
        time: float,
    ) -> RouteResult:
        """Compute a high-transmittance OOS path without memory penalties."""

        edges = tuple(_routing_edges(graph, request))
        adjacency = _weighted_adjacency(edges)
        path, cost = _minimum_weight_path(
            adjacency,
            request.source,
            request.destination,
        )
        if not path:
            return RouteResult(
                success=False,
                reason="no OOS path found",
            )

        probability = path_transmittance_product(path, edges)
        return RouteResult(
            path=path,
            success=True,
            cost=cost,
            success_probability=probability,
            reason=None,
            metadata={"routing": self.name},
        )


def _routing_edges(graph: Any, request: EntanglementRequest) -> Iterable[Any]:
    edge_attributes = request.metadata.get("edge_attributes")
    if edge_attributes is not None:
        return edge_attributes
    return graph.available_edges


def _weighted_adjacency(
    edges: Iterable[Any],
) -> Dict[str, Tuple[Tuple[str, float], ...]]:
    adjacency: Dict[str, List[Tuple[str, float]]] = {}
    for edge in edges:
        if not getattr(edge, "available", True):
            continue
        first, second = _endpoints(edge)
        weight = safe_negative_log(_edge_probability(edge))
        if isinf(weight):
            continue
        adjacency.setdefault(first, []).append((second, weight))
        adjacency.setdefault(second, []).append((first, weight))

    return {
        node: tuple(sorted(neighbors))
        for node, neighbors in sorted(adjacency.items())
    }


def _minimum_weight_path(
    adjacency: Dict[str, Tuple[Tuple[str, float], ...]],
    source: str,
    destination: str,
) -> Tuple[Tuple[str, ...], Optional[float]]:
    if source == destination:
        return (source,), 0.0
    if source not in adjacency:
        return (), None

    distances: Dict[str, float] = {source: 0.0}
    predecessors: Dict[str, Optional[str]] = {source: None}
    heap = [(0.0, source)]
    while heap:
        distance, node = heappop(heap)
        if distance > distances[node]:
            continue
        if node == destination:
            return (
                reconstruct_path(predecessors, source, destination),
                distance,
            )
        for neighbor, weight in adjacency.get(node, ()):
            candidate = distance + weight
            if candidate >= distances.get(neighbor, float("inf")):
                continue
            distances[neighbor] = candidate
            predecessors[neighbor] = node
            heappush(heap, (candidate, neighbor))

    return (), None


def _endpoints(edge: Any) -> Tuple[str, str]:
    endpoints = getattr(edge, "endpoints", None)
    if endpoints is None or len(endpoints) != 2:
        raise ValueError("edge must expose exactly two endpoints")
    return endpoints


def _edge_probability(edge: Any) -> float:
    success_probability = getattr(edge, "success_probability", None)
    if success_probability is not None:
        return success_probability
    transmittance = getattr(edge, "transmittance", None)
    if transmittance is None:
        return 1.0
    return transmittance
