"""Routing selection for the Simultaneous Downlink architecture."""

from __future__ import annotations

from typing import Iterable, Optional

from quasar.architecture.base import ArchitectureResult
from quasar.architecture.simultaneous_downlink import (
    SimultaneousDownlinkArchitecture,
)
from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.utils import safe_negative_log


class SDRouter(Router):
    """Select the best memoryless simultaneous dual-downlink opportunity."""

    name = "sd"

    def __init__(
        self,
        architecture: Optional[SimultaneousDownlinkArchitecture] = None,
    ) -> None:
        self.architecture = architecture or SimultaneousDownlinkArchitecture()

    def compute_route(
        self,
        graph,
        request: EntanglementRequest,
        time: float,
    ) -> RouteResult:
        """Select the feasible SD opportunity with maximum joint loss score."""

        opportunities = tuple(
            opportunity
            for opportunity in self.architecture.find_opportunities(
                graph,
                request,
                time,
            )
            if opportunity.feasible
        )
        selected = _best_opportunity(opportunities)
        if selected is None:
            return RouteResult(
                success=False,
                storage_delay=0.0,
                reason="no simultaneous downlink opportunity",
                metadata={"opportunities": opportunities},
            )

        probability = selected.success_probability
        if probability is None:
            probability = 0.0
        return RouteResult(
            success=True,
            cost=safe_negative_log(probability),
            success_probability=probability,
            storage_delay=0.0,
            reason=None,
            metadata={
                "selected_opportunity": selected,
                "opportunities": opportunities,
                "score": probability,
            },
        )


def _best_opportunity(
    opportunities: Iterable[ArchitectureResult],
) -> Optional[ArchitectureResult]:
    best = None
    best_score = -1.0
    for opportunity in opportunities:
        score = opportunity.success_probability
        if score is None:
            score = 0.0
        if score > best_score:
            best = opportunity
            best_score = score
    return best
