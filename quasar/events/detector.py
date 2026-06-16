"""Threshold-crossing detector for QUASAR event records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from quasar.events.record import EventRecord
from quasar.events.types import EventType


EdgeKey = Tuple[str, str]


@dataclass(frozen=True)
class EventThresholds:
    """Thresholds used by the QUASAR event detector."""

    channel_quality_threshold: float = 0.0
    fidelity_threshold: float = 0.75

    def __post_init__(self) -> None:
        _validate_probability(
            self.channel_quality_threshold,
            "channel_quality_threshold",
        )
        _validate_probability(self.fidelity_threshold, "fidelity_threshold")


class ThresholdCrossingDetector:
    """Detect physical-state crossings without scheduling or recomputation."""

    def detect(
        self,
        previous_state: Any,
        current_state: Any,
        current_route: Any = None,
        thresholds: Any = None,
    ) -> List[EventRecord]:
        """Return event records caused by previous/current state crossings."""

        event_thresholds = _coerce_thresholds(thresholds)
        time = _state_time(current_state)
        previous_edges = _edge_table(previous_state)
        current_edges = _edge_table(current_state)
        events: List[EventRecord] = []

        for edge_key in sorted(set(previous_edges).union(current_edges)):
            previous_edge = previous_edges.get(edge_key)
            current_edge = current_edges.get(edge_key)
            events.extend(
                self._detect_edge_events(
                    edge_key,
                    previous_edge,
                    current_edge,
                    time,
                    event_thresholds,
                )
            )

        if _available_edge_set(previous_edges) != _available_edge_set(current_edges):
            events.append(
                EventRecord(
                    event_type=EventType.GRAPH_UPDATE,
                    time=time,
                    previous_value=tuple(sorted(_available_edge_set(previous_edges))),
                    current_value=tuple(sorted(_available_edge_set(current_edges))),
                    reason="available edge set changed",
                )
            )

        route_event = self._detect_route_recompute(time, current_route, events)
        if route_event is not None:
            events.append(route_event)
        return events

    def _detect_edge_events(
        self,
        edge_key: EdgeKey,
        previous_edge: Any,
        current_edge: Any,
        time: float,
        thresholds: EventThresholds,
    ) -> List[EventRecord]:
        events: List[EventRecord] = []
        previous_available = _edge_available(previous_edge)
        current_available = _edge_available(current_edge)

        if not previous_available and current_available:
            events.append(
                EventRecord(
                    event_type=EventType.LINK_UP,
                    time=time,
                    endpoints=edge_key,
                    previous_value=previous_available,
                    current_value=current_available,
                    reason="link became available",
                )
            )
        elif previous_available and not current_available:
            events.append(
                EventRecord(
                    event_type=EventType.LINK_DROP,
                    time=time,
                    endpoints=edge_key,
                    previous_value=previous_available,
                    current_value=current_available,
                    reason="link became unavailable",
                )
            )

        events.extend(
            _threshold_events(
                edge_key=edge_key,
                time=time,
                previous_value=_edge_fidelity(previous_edge),
                current_value=_edge_fidelity(current_edge),
                threshold=thresholds.fidelity_threshold,
                loss_type=EventType.FIDELITY_LOSS,
                recovery_type=EventType.FIDELITY_RECOVERY,
                loss_reason="fidelity crossed below threshold",
                recovery_reason="fidelity recovered above threshold",
            )
        )
        events.extend(
            _threshold_events(
                edge_key=edge_key,
                time=time,
                previous_value=_edge_channel_quality(previous_edge),
                current_value=_edge_channel_quality(current_edge),
                threshold=thresholds.channel_quality_threshold,
                loss_type=EventType.CHANNEL_DEGRADATION,
                recovery_type=EventType.CHANNEL_RECOVERY,
                loss_reason="channel quality crossed below threshold",
                recovery_reason="channel quality recovered above threshold",
            )
        )
        return events

    def _detect_route_recompute(
        self,
        time: float,
        current_route: Any,
        events: Iterable[EventRecord],
    ) -> Optional[EventRecord]:
        route_edges = _route_edge_set(current_route)
        if not route_edges:
            return None
        impacted_events = [
            event
            for event in events
            if event.event_type
            in (
                EventType.LINK_DROP,
                EventType.CHANNEL_DEGRADATION,
                EventType.FIDELITY_LOSS,
            )
            and event.endpoints in route_edges
        ]
        if not impacted_events:
            return None
        return EventRecord(
            event_type=EventType.ROUTE_RECOMPUTE,
            time=time,
            previous_value=None,
            current_value=tuple(sorted(route_edges)),
            reason="current route uses a failed edge",
            metadata={
                "impacted_edges": tuple(event.endpoints for event in impacted_events),
                "triggering_events": tuple(event.event_type for event in impacted_events),
            },
        )


def _threshold_events(
    edge_key: EdgeKey,
    time: float,
    previous_value: Optional[float],
    current_value: Optional[float],
    threshold: float,
    loss_type: EventType,
    recovery_type: EventType,
    loss_reason: str,
    recovery_reason: str,
) -> List[EventRecord]:
    if previous_value is None or current_value is None:
        return []
    if previous_value >= threshold and current_value < threshold:
        return [
            EventRecord(
                event_type=loss_type,
                time=time,
                endpoints=edge_key,
                previous_value=previous_value,
                current_value=current_value,
                threshold=threshold,
                reason=loss_reason,
            )
        ]
    if previous_value < threshold and current_value >= threshold:
        return [
            EventRecord(
                event_type=recovery_type,
                time=time,
                endpoints=edge_key,
                previous_value=previous_value,
                current_value=current_value,
                threshold=threshold,
                reason=recovery_reason,
            )
        ]
    return []


def _coerce_thresholds(thresholds: Any) -> EventThresholds:
    if thresholds is None:
        return EventThresholds()
    if isinstance(thresholds, EventThresholds):
        return thresholds
    channel_threshold = thresholds.get(
        "channel_quality_threshold",
        thresholds.get("transmittance_threshold", 0.0),
    )
    fidelity_threshold = thresholds.get("fidelity_threshold", 0.75)
    return EventThresholds(
        channel_quality_threshold=channel_threshold,
        fidelity_threshold=fidelity_threshold,
    )


def _state_time(state: Any) -> float:
    if state is None:
        return 0.0
    if isinstance(state, Mapping):
        return state.get("time", 0.0)
    return getattr(state, "time", 0.0)


def _edge_table(state: Any) -> Dict[EdgeKey, Any]:
    edges = _state_edges(state)
    table: Dict[EdgeKey, Any] = {}
    for key, edge in edges:
        endpoints = _edge_endpoints(edge, key)
        if endpoints is not None:
            table[_edge_key(endpoints)] = edge
    return table


def _state_edges(state: Any) -> Iterable[Tuple[Any, Any]]:
    if state is None:
        return ()
    if isinstance(state, Mapping):
        if "edges" in state:
            return tuple((None, edge) for edge in state["edges"])
        if "edge_attributes" in state:
            return tuple((None, edge) for edge in state["edge_attributes"])
        return tuple(state.items())
    if hasattr(state, "edges"):
        return tuple((None, edge) for edge in state.edges)
    if hasattr(state, "edge_attributes"):
        return tuple((None, edge) for edge in state.edge_attributes)
    return tuple((None, edge) for edge in state)


def _edge_endpoints(edge: Any, fallback_key: Any = None) -> Optional[Tuple[str, str]]:
    endpoints = _edge_value(edge, "endpoints")
    if endpoints is None and _looks_like_endpoints(fallback_key):
        endpoints = fallback_key
    if endpoints is None:
        return None
    if len(endpoints) != 2:
        raise ValueError("edge endpoints must contain exactly two nodes")
    first, second = endpoints
    if not first or not second:
        raise ValueError("edge endpoints must be non-empty")
    return first, second


def _edge_key(endpoints: Tuple[str, str]) -> EdgeKey:
    first, second = endpoints
    return tuple(sorted((first, second)))


def _looks_like_endpoints(value: Any) -> bool:
    return isinstance(value, tuple) and len(value) == 2


def _available_edge_set(edges: Mapping[EdgeKey, Any]) -> set:
    return {
        edge_key
        for edge_key, edge in edges.items()
        if _edge_available(edge)
    }


def _edge_available(edge: Any) -> bool:
    if edge is None:
        return False
    value = _edge_value(edge, "available")
    if value is None:
        return True
    return bool(value)


def _edge_fidelity(edge: Any) -> Optional[float]:
    return _optional_probability(_edge_value(edge, "fidelity"), "fidelity")


def _edge_channel_quality(edge: Any) -> Optional[float]:
    success_probability = _edge_value(edge, "success_probability")
    if success_probability is not None:
        return _optional_probability(success_probability, "success_probability")
    return _optional_probability(_edge_value(edge, "transmittance"), "transmittance")


def _edge_value(edge: Any, name: str) -> Any:
    if edge is None:
        return None
    if isinstance(edge, Mapping):
        return edge.get(name)
    return getattr(edge, name, None)


def _optional_probability(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    _validate_probability(value, field_name)
    return value


def _route_edge_set(route: Any) -> set:
    path = _route_path(route)
    if len(path) < 2:
        return set()
    return {
        _edge_key((first, second))
        for first, second in zip(path, path[1:])
    }


def _route_path(route: Any) -> Tuple[str, ...]:
    if route is None:
        return ()
    if isinstance(route, Mapping):
        return tuple(route.get("path", ()))
    if isinstance(route, (tuple, list)):
        return tuple(route)
    path = getattr(route, "path_tuple", None)
    if path is not None:
        return tuple(path)
    return tuple(getattr(route, "path", ()))


def _validate_probability(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
