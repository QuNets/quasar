"""Edge trace helpers for QUASAR metric collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class EdgeTraceRecord:
    """One recorded edge state sample."""

    time: float
    endpoints: Optional[Tuple[str, str]] = None
    edge_type: Optional[Any] = None
    available: bool = True
    transmittance: Optional[float] = None
    success_probability: Optional[float] = None
    fidelity: Optional[float] = None
    storage_delay: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")
        if self.endpoints is not None:
            if len(self.endpoints) != 2:
                raise ValueError("endpoints must contain exactly two nodes")
            first, second = self.endpoints
            if not first or not second:
                raise ValueError("endpoints must contain non-empty nodes")
            object.__setattr__(self, "endpoints", (first, second))
        _validate_optional_probability(self.transmittance, "transmittance")
        _validate_optional_probability(
            self.success_probability,
            "success_probability",
        )
        _validate_optional_probability(self.fidelity, "fidelity")
        if self.storage_delay is not None and self.storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")


@dataclass
class EdgeTrace:
    """Append-only trace of edge-level network attributes."""

    _records: list = field(default_factory=list)

    def record(
        self,
        time: float,
        edge: Any,
        attributes: Any = None,
        available: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EdgeTraceRecord:
        """Record edge attributes without recomputing physical values."""

        source = attributes if attributes is not None else edge
        record = EdgeTraceRecord(
            time=time,
            endpoints=_value(source, "endpoints", _edge_tuple(edge)),
            edge_type=_value(source, "edge_type", None),
            available=bool(_value(source, "available", available)),
            transmittance=_value(source, "transmittance", None),
            success_probability=_value(source, "success_probability", None),
            fidelity=_value(source, "fidelity", None),
            storage_delay=_value(source, "storage_delay", None),
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        return record

    @property
    def records(self) -> Tuple[EdgeTraceRecord, ...]:
        """Return recorded edge samples."""

        return tuple(self._records)

    def available_edge_ratio(self) -> float:
        """Return the fraction of recorded edges marked available."""

        if not self._records:
            return 0.0
        available_count = sum(1 for record in self._records if record.available)
        return available_count / len(self._records)

    def average_transmittance(self) -> Optional[float]:
        """Return the mean recorded transmittance."""

        return _average(record.transmittance for record in self._records)

    def average_success_probability(self) -> Optional[float]:
        """Return the mean recorded success probability."""

        return _average(record.success_probability for record in self._records)

    def average_fidelity(self) -> Optional[float]:
        """Return the mean recorded fidelity."""

        return _average(record.fidelity for record in self._records)

    def summary(self) -> dict:
        """Return a compact edge-trace summary."""

        return {
            "edge_record_count": len(self._records),
            "available_edge_ratio": self.available_edge_ratio(),
            "average_transmittance": self.average_transmittance(),
            "average_success_probability": self.average_success_probability(),
            "average_fidelity": self.average_fidelity(),
        }


def _value(source: Any, name: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _edge_tuple(edge: Any) -> Optional[Tuple[str, str]]:
    if isinstance(edge, tuple) and len(edge) == 2:
        return edge
    return None


def _average(values) -> Optional[float]:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _validate_optional_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
