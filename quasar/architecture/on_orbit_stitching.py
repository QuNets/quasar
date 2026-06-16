"""On-Orbit Stitching hardware abstraction."""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

from quasar.architecture.base import ArchitectureMode, ArchitectureResult, BaseArchitecture
from quasar.channel.probability import path_success_probability
from quasar.memory.decoherence import fidelity_after_storage, is_fidelity_feasible


class OnOrbitStitchingArchitecture(BaseArchitecture):
    """Memory-assisted OOS abstraction without path optimization."""

    name = "on_orbit_stitching"
    mode = ArchitectureMode.ON_ORBIT_STITCHING

    def __init__(
        self,
        initial_fidelity: float = 0.99,
        coherence_time: float = 0.1,
        fidelity_threshold: float = 0.75,
    ) -> None:
        self.initial_fidelity = initial_fidelity
        self.coherence_time = coherence_time
        self.fidelity_threshold = fidelity_threshold

    def find_opportunities(
        self,
        graph: Any,
        request: Any,
        time: float = 0.0,
    ) -> Sequence[ArchitectureResult]:
        """Evaluate one caller-provided stitching candidate.

        Stage 5 does not search for paths. Callers provide edge transmittances
        and storage delay through request metadata or a dictionary.
        """

        metadata = _request_metadata(request)
        return [
            self.evaluate_stitching_opportunity(
                edge_transmittances=metadata.get("edge_transmittances", ()),
                storage_delay=metadata.get("storage_delay", 0.0),
                swap_success_probabilities=metadata.get("swap_success_probabilities"),
                metadata=metadata,
            )
        ]

    def evaluate_stitching_opportunity(
        self,
        edge_transmittances: Iterable[float],
        storage_delay: float,
        swap_success_probabilities: Optional[Iterable[float]] = None,
        metadata: Optional[dict] = None,
    ) -> ArchitectureResult:
        """Return OOS feasibility for a supplied stitching candidate."""

        fidelity = fidelity_after_storage(
            delta_tau=storage_delay,
            f0=self.initial_fidelity,
            tau_c=self.coherence_time,
        )
        feasible = is_fidelity_feasible(fidelity, self.fidelity_threshold)
        transmittances = tuple(edge_transmittances)
        swap_probabilities = None
        if swap_success_probabilities is not None:
            swap_probabilities = tuple(swap_success_probabilities)
        success_probability = path_success_probability(transmittances, swap_probabilities)
        return ArchitectureResult(
            feasible=feasible,
            architecture=ArchitectureMode.ON_ORBIT_STITCHING,
            storage_delay=storage_delay,
            fidelity=fidelity,
            success_probability=success_probability,
            reason=None if feasible else "fidelity below threshold",
            metadata={
                **(metadata or {}),
                "edge_transmittances": transmittances,
                "swap_success_probabilities": swap_probabilities,
                "fidelity_threshold": self.fidelity_threshold,
            },
        )


def _request_metadata(request: Any) -> dict:
    if isinstance(request, dict):
        return dict(request.get("metadata", request))
    return dict(getattr(request, "metadata", {}))
