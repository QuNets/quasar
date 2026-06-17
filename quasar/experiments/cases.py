"""Reusable experiment case definitions for smoke batches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from quasar.experiments.config import (
    BaselineSimulationConfig,
    ControlledPairConfig,
    ExperimentConfig,
    WorkloadConfig,
)


DEFAULT_BATCH_TIME_POINTS = (
    0.0,
    300.0,
    600.0,
    900.0,
    1200.0,
    1500.0,
)


@dataclass(frozen=True)
class ExperimentCase:
    """Named wrapper around an ExperimentConfig."""

    name: str
    config: ExperimentConfig
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be non-empty")


def routing_baseline_cases(
    baseline: Optional[BaselineSimulationConfig] = None,
    controlled_pair: Optional[ControlledPairConfig] = None,
    time_points: Tuple[float, ...] = DEFAULT_BATCH_TIME_POINTS,
    planes: int = 6,
    satellites_per_plane: int = 10,
) -> Tuple[ExperimentCase, ...]:
    """Return OOS DSP/MPR/EASR cases over the same smoke-test setting."""

    baseline = baseline or BaselineSimulationConfig()
    controlled_pair = controlled_pair or ControlledPairConfig()
    cases = []
    for algorithm in ("dsp", "mpr", "easr"):
        config = ExperimentConfig(
            baseline=baseline,
            controlled_pair=controlled_pair,
            workload=WorkloadConfig(
                architecture="oos",
                routing_algorithm=algorithm,
                storage_delay_policy="zero_policy",
            ),
            time_points=time_points,
            planes=planes,
            satellites_per_plane=satellites_per_plane,
        )
        cases.append(
            ExperimentCase(
                name=f"OOS-{algorithm.upper()}",
                config=config,
                metadata={
                    "scenario_source": "WalkerDeltaLiteSource",
                    "storage_delay_source": "zero_policy",
                },
            )
        )
    return tuple(cases)
