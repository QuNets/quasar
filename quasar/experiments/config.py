"""Configuration models for paper-aligned QUASAR experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class BaselineSimulationConfig:
    """Baseline physical parameters aligned with the QUASAR paper."""

    altitude_km: float = 500.0
    inclination_deg: float = 53.0
    dt: float = 0.1
    min_elevation_deg: float = 15.0
    eta0: float = 1e-3
    alpha: float = 0.01
    h0_km: float = 20.0
    kappa: float = 0.85
    zeta_swap: float = 0.60
    f0: float = 0.99
    fidelity_threshold: float = 0.75
    tau_c: float = 0.1

    def __post_init__(self) -> None:
        for field_name in ("altitude_km", "dt", "eta0", "h0_km", "kappa", "tau_c"):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive")
        if not 0.0 <= self.inclination_deg <= 180.0:
            raise ValueError("inclination_deg must be in [0, 180]")
        if not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")
        if self.alpha < 0:
            raise ValueError("alpha must be non-negative")
        for field_name in ("zeta_swap", "f0", "fidelity_threshold"):
            if not 0.0 <= getattr(self, field_name) <= 1.0:
                raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass(frozen=True)
class ControlledPairConfig:
    """Controlled Houston to Washington-DC ground-station pair."""

    source_name: str = "Houston"
    source_latitude_deg: float = 29.7604
    source_longitude_deg: float = -95.3698
    destination_name: str = "Washington-DC"
    destination_latitude_deg: float = 38.9072
    destination_longitude_deg: float = -77.0369

    def __post_init__(self) -> None:
        if not self.source_name:
            raise ValueError("source_name must be non-empty")
        if not self.destination_name:
            raise ValueError("destination_name must be non-empty")
        if self.source_name == self.destination_name:
            raise ValueError("source and destination must be distinct")
        for field_name in ("source_latitude_deg", "destination_latitude_deg"):
            if not -90.0 <= getattr(self, field_name) <= 90.0:
                raise ValueError(f"{field_name} must be in [-90, 90]")
        for field_name in ("source_longitude_deg", "destination_longitude_deg"):
            if not -180.0 <= getattr(self, field_name) <= 180.0:
                raise ValueError(f"{field_name} must be in [-180, 180]")


@dataclass(frozen=True)
class WorkloadConfig:
    """Architecture and routing workload selection."""

    architecture: str = "oos"
    routing_algorithm: str = "easr"
    storage_delay_policy: str = "zero_policy"
    synthetic_storage_delay: float = 0.0
    temporal_penalty_xi: float = 1.0

    def __post_init__(self) -> None:
        architecture = self.architecture.lower()
        routing_algorithm = self.routing_algorithm.lower()
        if architecture not in ("sd", "oos"):
            raise ValueError("architecture must be 'sd' or 'oos'")
        if architecture == "sd" and routing_algorithm != "sd":
            raise ValueError("SD architecture requires the sd router")
        if architecture == "oos" and routing_algorithm not in ("dsp", "mpr", "easr"):
            raise ValueError("OOS architecture requires dsp, mpr, or easr")
        allowed_storage_delay_policies = (
            "zero_policy",
            "synthetic_demo",
            "contact_window_age",
        )
        if self.storage_delay_policy not in allowed_storage_delay_policies:
            raise ValueError(
                "storage_delay_policy must be zero_policy, synthetic_demo, "
                "or contact_window_age"
            )
        if self.synthetic_storage_delay < 0:
            raise ValueError("synthetic_storage_delay must be non-negative")
        if self.temporal_penalty_xi < 0:
            raise ValueError("temporal_penalty_xi must be non-negative")


@dataclass(frozen=True)
class ExperimentConfig:
    """Small explicit-time experiment configuration."""

    baseline: BaselineSimulationConfig = field(default_factory=BaselineSimulationConfig)
    controlled_pair: ControlledPairConfig = field(default_factory=ControlledPairConfig)
    workload: WorkloadConfig = field(default_factory=WorkloadConfig)
    time_points: Tuple[float, ...] = (0.0, 0.1, 0.2)
    planes: int = 4
    satellites_per_plane: int = 5
    max_sgl_range_km: Optional[float] = None
    max_isl_range_km: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.time_points:
            raise ValueError("time_points must not be empty")
        if any(time < 0 for time in self.time_points):
            raise ValueError("time_points must be non-negative")
        if tuple(sorted(self.time_points)) != tuple(self.time_points):
            raise ValueError("time_points must be sorted")
        if self.planes <= 0:
            raise ValueError("planes must be positive")
        if self.satellites_per_plane <= 0:
            raise ValueError("satellites_per_plane must be positive")
        for field_name in ("max_sgl_range_km", "max_isl_range_km"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

    @property
    def architecture(self) -> str:
        """Return the selected architecture."""

        return self.workload.architecture

    @property
    def routing_algorithm(self) -> str:
        """Return the selected routing algorithm."""

        return self.workload.routing_algorithm
