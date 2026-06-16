"""EDR-aware spatiotemporal routing for OOS paths."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import exp, isinf
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from quasar.memory.decoherence import fidelity_after_storage, is_fidelity_feasible
from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.utils import reconstruct_path, safe_negative_log


@dataclass(frozen=True)
class _EASRContext:
    tau_c: float
    xi: float
    initial_fidelity: float
    fidelity_threshold: float
    default_swap_success_probability: float
    storage_delays: Mapping[Any, float]
    swap_success_probabilities: Mapping[Any, float]
    destination: str


class OOSEASRRouter(Router):
    """OOS-only EASR router balancing spatial loss and storage delay."""

    name = "oos_easr"

    def __init__(
        self,
        tau_c: float = 0.1,
        xi: float = 1.0,
        initial_fidelity: float = 0.99,
        fidelity_threshold: float = 0.75,
        default_swap_success_probability: float = 1.0,
    ) -> None:
        _validate_positive(tau_c, "tau_c")
        _validate_non_negative(xi, "xi")
        _validate_probability(initial_fidelity, "initial_fidelity")
        _validate_probability(fidelity_threshold, "fidelity_threshold")
        _validate_probability(
            default_swap_success_probability,
            "default_swap_success_probability",
        )
        self.tau_c = tau_c
        self.xi = xi
        self.initial_fidelity = initial_fidelity
        self.fidelity_threshold = fidelity_threshold
        self.default_swap_success_probability = default_swap_success_probability

    def compute_route(
        self,
        graph,
        request: EntanglementRequest,
        time: float,
    ) -> RouteResult:
        """Compute an OOS path using the EASR additive edge weight."""

        edges = tuple(_routing_edges(graph, request))
        context = _context_from_request(self, request)
        adjacency = _weighted_adjacency(edges, context)
        path, cost = _minimum_weight_path(
            adjacency,
            request.source,
            request.destination,
        )
        if not path:
            return RouteResult(
                success=False,
                reason="no OOS EASR path found",
                metadata={"routing": self.name},
            )

        score = easr_path_score(path, edges, context)
        fidelity = fidelity_after_storage(
            delta_tau=score["storage_delay"],
            f0=self.initial_fidelity,
            tau_c=self.tau_c,
        )
        if not is_fidelity_feasible(fidelity, self.fidelity_threshold):
            return RouteResult(
                path=path,
                success=False,
                cost=cost,
                success_probability=score["success_probability"],
                fidelity=fidelity,
                storage_delay=score["storage_delay"],
                reason="fidelity below threshold",
                metadata={
                    "routing": self.name,
                    "objective_score": score["objective_score"],
                },
            )

        return RouteResult(
            path=path,
            success=True,
            cost=cost,
            success_probability=score["success_probability"],
            fidelity=fidelity,
            storage_delay=score["storage_delay"],
            reason=None,
            metadata={
                "routing": self.name,
                "objective_score": score["objective_score"],
            },
        )


def easr_edge_weight(
    edge: Any,
    tau_c: float,
    xi: float = 1.0,
    swap_success_probability: float = 1.0,
    storage_delay: Optional[float] = None,
) -> float:
    """Return ``-ln eta - ln zeta + xi * storage_delay / tau_c``."""

    _validate_positive(tau_c, "tau_c")
    _validate_non_negative(xi, "xi")
    _validate_probability(swap_success_probability, "swap_success_probability")
    delay = _edge_storage_delay(edge) if storage_delay is None else storage_delay
    _validate_non_negative(delay, "storage_delay")
    return (
        safe_negative_log(_edge_transmittance(edge))
        + safe_negative_log(swap_success_probability)
        + xi * delay / tau_c
    )


def easr_path_score(
    path: Sequence[str],
    edges: Iterable[Any],
    context: _EASRContext,
) -> Dict[str, float]:
    """Return EASR path score terms for a concrete OOS path."""

    edge_map = _edge_map(edges)
    success_probability = 1.0
    storage_delay = 0.0
    for first, second in zip(path, path[1:]):
        edge = edge_map.get((first, second))
        if edge is None:
            raise ValueError(f"missing edge attributes for {first!r}->{second!r}")
        success_probability *= _edge_transmittance(edge)
        success_probability *= _swap_success_probability(edge, second, context)
        storage_delay += _storage_delay(edge, second, context)

    objective_score = success_probability * exp(
        -context.xi * storage_delay / context.tau_c,
    )
    return {
        "success_probability": success_probability,
        "storage_delay": storage_delay,
        "objective_score": objective_score,
    }


def _context_from_request(
    router: OOSEASRRouter,
    request: EntanglementRequest,
) -> _EASRContext:
    metadata = request.metadata
    return _EASRContext(
        tau_c=router.tau_c,
        xi=router.xi,
        initial_fidelity=router.initial_fidelity,
        fidelity_threshold=router.fidelity_threshold,
        default_swap_success_probability=metadata.get(
            "swap_success_probability",
            metadata.get(
                "zeta_swap",
                router.default_swap_success_probability,
            ),
        ),
        storage_delays=dict(metadata.get("storage_delays", {})),
        swap_success_probabilities=dict(
            metadata.get("swap_success_probabilities", {}),
        ),
        destination=request.destination,
    )


def _routing_edges(graph: Any, request: EntanglementRequest) -> Iterable[Any]:
    edge_attributes = request.metadata.get("edge_attributes")
    if edge_attributes is not None:
        return edge_attributes
    return graph.available_edges


def _weighted_adjacency(
    edges: Iterable[Any],
    context: _EASRContext,
) -> Dict[str, Tuple[Tuple[str, float], ...]]:
    adjacency: Dict[str, List[Tuple[str, float]]] = {}
    for edge in edges:
        if not getattr(edge, "available", True):
            continue
        first, second = _endpoints(edge)
        _add_directed_edge(adjacency, first, second, edge, context)
        _add_directed_edge(adjacency, second, first, edge, context)
    return {
        node: tuple(sorted(neighbors))
        for node, neighbors in sorted(adjacency.items())
    }


def _add_directed_edge(
    adjacency: Dict[str, List[Tuple[str, float]]],
    first: str,
    second: str,
    edge: Any,
    context: _EASRContext,
) -> None:
    storage_delay = _storage_delay(edge, second, context)
    fidelity = fidelity_after_storage(
        delta_tau=storage_delay,
        f0=context.initial_fidelity,
        tau_c=context.tau_c,
    )
    if not is_fidelity_feasible(fidelity, context.fidelity_threshold):
        return
    weight = easr_edge_weight(
        edge=edge,
        tau_c=context.tau_c,
        xi=context.xi,
        swap_success_probability=_swap_success_probability(edge, second, context),
        storage_delay=storage_delay,
    )
    if isinf(weight):
        return
    adjacency.setdefault(first, []).append((second, weight))


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


def _edge_map(edges: Iterable[Any]) -> Dict[Tuple[str, str], Any]:
    edge_map: Dict[Tuple[str, str], Any] = {}
    for edge in edges:
        if not getattr(edge, "available", True):
            continue
        first, second = _endpoints(edge)
        edge_map[(first, second)] = edge
        edge_map[(second, first)] = edge
    return edge_map


def _endpoints(edge: Any) -> Tuple[str, str]:
    endpoints = getattr(edge, "endpoints", None)
    if endpoints is None or len(endpoints) != 2:
        raise ValueError("edge must expose exactly two endpoints")
    first, second = endpoints
    if not first or not second:
        raise ValueError("edge endpoints must be non-empty")
    return first, second


def _edge_transmittance(edge: Any) -> float:
    transmittance = getattr(edge, "transmittance", None)
    if transmittance is None:
        transmittance = getattr(edge, "success_probability", None)
    if transmittance is None:
        return 1.0
    _validate_probability(transmittance, "edge transmittance")
    return transmittance


def _edge_storage_delay(edge: Any) -> float:
    storage_delay = getattr(edge, "storage_delay", None)
    if storage_delay is None:
        metadata = getattr(edge, "metadata", {})
        storage_delay = metadata.get("storage_delay", 0.0)
    _validate_non_negative(storage_delay, "storage_delay")
    return storage_delay


def _storage_delay(edge: Any, target_node: str, context: _EASRContext) -> float:
    delay = _lookup_by_edge_or_node(context.storage_delays, edge, target_node)
    if delay is None:
        delay = _edge_storage_delay(edge)
    _validate_non_negative(delay, "storage_delay")
    return delay


def _swap_success_probability(
    edge: Any,
    target_node: str,
    context: _EASRContext,
) -> float:
    if target_node == context.destination:
        return 1.0
    probability = _lookup_by_edge_or_node(
        context.swap_success_probabilities,
        edge,
        target_node,
    )
    if probability is None:
        probability = _edge_swap_success_probability(edge)
    if probability is None:
        probability = context.default_swap_success_probability
    _validate_probability(probability, "swap_success_probability")
    return probability


def _edge_swap_success_probability(edge: Any) -> Optional[float]:
    probability = getattr(edge, "swap_success_probability", None)
    if probability is None:
        probability = getattr(edge, "zeta_swap", None)
    if probability is None:
        metadata = getattr(edge, "metadata", {})
        probability = metadata.get(
            "swap_success_probability",
            metadata.get("zeta_swap"),
        )
    return probability


def _lookup_by_edge_or_node(
    values: Mapping[Any, float],
    edge: Any,
    target_node: str,
) -> Optional[float]:
    if not values:
        return None
    first, second = _endpoints(edge)
    candidates = (
        target_node,
        (first, second),
        (second, first),
        f"{first}->{second}",
        f"{second}->{first}",
    )
    for candidate in candidates:
        if candidate in values:
            return values[candidate]
    return None


def _validate_probability(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _validate_positive(value: float, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_non_negative(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
