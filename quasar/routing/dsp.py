"""Dynamic Shortest Path baseline for OOS routing."""

from __future__ import annotations

from quasar.routing.base import EntanglementRequest, RouteResult, Router
from quasar.routing.utils import build_adjacency, shortest_hop_path


class OOSDSPRouter(Router):
    """OOS-only baseline that minimizes instantaneous hop count."""

    name = "oos_dsp"

    def compute_route(
        self,
        graph,
        request: EntanglementRequest,
        time: float,
    ) -> RouteResult:
        """Compute a minimum-hop path over available OOS graph edges."""

        adjacency = build_adjacency(graph.available_edges)
        path = shortest_hop_path(adjacency, request.source, request.destination)
        if not path:
            return RouteResult(
                success=False,
                reason="no OOS path found",
            )

        return RouteResult(
            path=path,
            success=True,
            cost=float(len(path) - 1),
            reason=None,
            metadata={"routing": self.name},
        )
