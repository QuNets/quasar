"""Minimal spatiotemporal topology engine for QUASAR."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.topology.graph import TopologySnapshot
from quasar.topology.visibility import apply_visibility_mask


class SpatiotemporalTopologyEngine:
    """Build G(t) from candidate links using visibility and range pruning.

    This stage intentionally does not implement SGP4, TLE parsing, Walker-Delta
    generation, channel transmittance, memory, architecture, or routing logic.
    Candidate links are supplied by the caller and treated as a simplified
    physical snapshot at ``time``.
    """

    def __init__(
        self,
        satellites: Iterable[Satellite],
        ground_stations: Iterable[GroundStation],
        min_elevation_deg: float = 15.0,
        max_sgl_range_km: Optional[float] = None,
        max_isl_range_km: Optional[float] = None,
    ) -> None:
        self.satellites = tuple(satellites)
        self.ground_stations = tuple(ground_stations)
        self.min_elevation_deg = min_elevation_deg
        self.max_sgl_range_km = max_sgl_range_km
        self.max_isl_range_km = max_isl_range_km
        self.nodes = self._build_node_names(self.satellites, self.ground_stations)
        self._validate_parameters()

    def build_snapshot(
        self,
        time: float,
        candidate_links: Iterable[LinkState],
    ) -> TopologySnapshot:
        """Return a topology snapshot after pruning infeasible links."""

        if time < 0:
            raise ValueError("time must be non-negative")

        pruned_edges = []
        for link_state in candidate_links:
            self._validate_candidate_link(link_state)
            pruned_edges.append(
                apply_visibility_mask(
                    link_state,
                    min_elevation_deg=self.min_elevation_deg,
                    max_range_km=self._range_constraint(link_state.edge_type),
                )
            )

        return TopologySnapshot(time=time, nodes=self.nodes, edges=tuple(pruned_edges))

    def _validate_parameters(self) -> None:
        if not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")
        for field_name, value in (
            ("max_sgl_range_km", self.max_sgl_range_km),
            ("max_isl_range_km", self.max_isl_range_km),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

    def _validate_candidate_link(self, link_state: LinkState) -> None:
        unknown = [node for node in link_state.endpoints if node not in self.nodes]
        if unknown:
            raise ValueError(f"candidate link references unknown nodes: {unknown}")

    def _range_constraint(self, edge_type: EdgeType) -> Optional[float]:
        if edge_type == EdgeType.SGL:
            return self.max_sgl_range_km
        if edge_type == EdgeType.ISL:
            return self.max_isl_range_km
        raise ValueError(f"unsupported edge type: {edge_type}")

    @staticmethod
    def _build_node_names(
        satellites: Sequence[Satellite],
        ground_stations: Sequence[GroundStation],
    ) -> Tuple[str, ...]:
        nodes = tuple(node.name for node in satellites) + tuple(node.name for node in ground_stations)
        if len(set(nodes)) != len(nodes):
            raise ValueError("satellites and ground stations must have unique names")
        return nodes
