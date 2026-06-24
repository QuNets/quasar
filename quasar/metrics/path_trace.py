"""Path trace helpers for QUASAR metric collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class PathTraceRecord:
    """One recorded routing result sample."""

    time: float
    path: Tuple[str, ...] = field(default_factory=tuple)
    success: bool = False
    cost: Optional[float] = None
    success_probability: Optional[float] = None
    storage_delay: Optional[float] = None
    fidelity: Optional[float] = None
    request: Any = None
    architecture: Optional[str] = None
    algorithm: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError("time must be non-negative")
        object.__setattr__(self, "path", tuple(self.path))
        for idx, node in enumerate(self.path):
            if not node:
                raise ValueError(f"path[{idx}] must be a non-empty string")
        if self.cost is not None and self.cost < 0:
            raise ValueError("cost must be non-negative")
        _validate_optional_probability(
            self.success_probability,
            "success_probability",
        )
        _validate_optional_probability(self.fidelity, "fidelity")
        if self.storage_delay is not None and self.storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")


@dataclass
class PathTrace:
    """Append-only trace of route results and selected opportunities."""

    _records: list = field(default_factory=list)

    def record(
        self,
        time: float,
        route_result: Any = None,
        request: Any = None,
        architecture: Optional[str] = None,
        algorithm: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PathTraceRecord:
        """Record a routing result without recomputing a path."""

        result_metadata = dict(_value(route_result, "metadata", {}) or {})
        result_metadata.update(metadata or {})
        record = PathTraceRecord(
            time=time,
            path=_path(route_result),
            success=bool(_value(route_result, "success", False)),
            cost=_value(route_result, "cost", None),
            success_probability=_value(route_result, "success_probability", None),
            storage_delay=_value(route_result, "storage_delay", None),
            fidelity=_value(route_result, "fidelity", None),
            request=request,
            architecture=architecture,
            algorithm=algorithm,
            metadata=result_metadata,
        )
        self._records.append(record)
        return record

    @property
    def records(self) -> Tuple[PathTraceRecord, ...]:
        """Return recorded path samples."""

        return tuple(self._records)

    def success_rate(self) -> float:
        """Return the fraction of successful recorded routes."""

        if not self._records:
            return 0.0
        success_count = sum(1 for record in self._records if record.success)
        return success_count / len(self._records)

    def average_cost(self) -> Optional[float]:
        """Return the mean recorded routing cost."""

        return _average(record.cost for record in self._records)

    def summary(self) -> dict:
        """Return a compact path-trace summary."""

        return {
            "path_count": len(self._records),
            "routing_success_rate": self.success_rate(),
            "average_cost": self.average_cost(),
        }


def _value(source: Any, name: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _path(route_result: Any) -> Tuple[str, ...]:
    path_tuple = _value(route_result, "path_tuple", None)
    if path_tuple is not None:
        return tuple(path_tuple)
    return tuple(_value(route_result, "path", ()))


def _average(values) -> Optional[float]:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _validate_optional_probability(value: Optional[float], field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
