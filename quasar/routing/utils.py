"""Small graph helpers used by QUASAR routing workloads."""

from __future__ import annotations

from collections import deque
from math import inf, log
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


Adjacency = Dict[str, Tuple[str, ...]]
Predecessors = Mapping[str, Optional[str]]


def build_adjacency(edges: Iterable[Any], directed: bool = False) -> Adjacency:
    """Build a deterministic adjacency map from edge-like objects."""

    adjacency: Dict[str, List[str]] = {}
    for edge in edges:
        if not _edge_available(edge):
            continue
        first, second = _edge_endpoints(edge)
        adjacency.setdefault(first, []).append(second)
        adjacency.setdefault(second, [])
        if not directed:
            adjacency[second].append(first)

    return {
        node: tuple(sorted(set(neighbors)))
        for node, neighbors in sorted(adjacency.items())
    }


def reconstruct_path(
    predecessors: Predecessors,
    source: str,
    destination: str,
) -> Tuple[str, ...]:
    """Reconstruct a path from a predecessor map."""

    if source == destination:
        return (source,)
    if destination not in predecessors:
        return ()

    path = [destination]
    current = destination
    while current != source:
        previous = predecessors.get(current)
        if previous is None:
            return ()
        path.append(previous)
        current = previous

    return tuple(reversed(path))


def path_transmittance_product(
    path: Sequence[str],
    edges: Iterable[Any],
) -> float:
    """Return the product of transmittances along a concrete path."""

    if len(path) < 2:
        return 1.0

    edge_map = _edge_map(edges)
    product = 1.0
    for first, second in zip(path, path[1:]):
        edge = edge_map.get((first, second))
        if edge is None:
            raise ValueError(f"missing edge attributes for {first!r}->{second!r}")
        product *= _edge_transmittance(edge)
    return product


def safe_negative_log(probability: float) -> float:
    """Return ``-log(probability)`` with zero mapped to infinity."""

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    if probability == 0.0:
        return inf
    return -log(probability)


def shortest_hop_path(
    adjacency: Mapping[str, Iterable[str]],
    source: str,
    destination: str,
) -> Tuple[str, ...]:
    """Return the minimum-hop path in an unweighted graph."""

    if source == destination:
        return (source,)
    if source not in adjacency:
        return ()

    predecessors: Dict[str, Optional[str]] = {source: None}
    queue = deque([source])
    while queue:
        current = queue.popleft()
        for neighbor in sorted(adjacency.get(current, ())):
            if neighbor in predecessors:
                continue
            predecessors[neighbor] = current
            if neighbor == destination:
                return reconstruct_path(predecessors, source, destination)
            queue.append(neighbor)

    return ()


def _edge_available(edge: Any) -> bool:
    return bool(getattr(edge, "available", True))


def _edge_endpoints(edge: Any) -> Tuple[str, str]:
    endpoints = getattr(edge, "endpoints", None)
    if endpoints is None or len(endpoints) != 2:
        raise ValueError("edge must expose exactly two endpoints")
    first, second = endpoints
    if not first or not second:
        raise ValueError("edge endpoints must be non-empty")
    return first, second


def _edge_map(edges: Iterable[Any]) -> Dict[Tuple[str, str], Any]:
    edge_map: Dict[Tuple[str, str], Any] = {}
    for edge in edges:
        if not _edge_available(edge):
            continue
        first, second = _edge_endpoints(edge)
        edge_map[(first, second)] = edge
        edge_map[(second, first)] = edge
    return edge_map


def _edge_transmittance(edge: Any) -> float:
    transmittance = getattr(edge, "transmittance", None)
    if transmittance is None:
        transmittance = getattr(edge, "success_probability", None)
    if transmittance is None:
        return 1.0
    if not 0.0 <= transmittance <= 1.0:
        raise ValueError("edge transmittance must be in [0, 1]")
    return transmittance
