"""Small paper-aligned end-to-end experiment runner."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Tuple

from quasar.channel.loss import total_transmittance
from quasar.channel.models import EdgeAttributes
from quasar.channel.probability import path_success_probability
from quasar.events import EventBridge
from quasar.experiments.baseline import houston_washington_pair
from quasar.experiments.config import ExperimentConfig
from quasar.experiments.result import ExperimentResult
from quasar.experiments.workload import FixedPairWorkload
from quasar.memory.decoherence import fidelity_after_storage
from quasar.metrics import EdgeTrace, EventLog, MetricSummary, PathTrace
from quasar.routing import OOSDSPRouter, OOSEASRRouter, OOSMPRRouter, SDRouter
from quasar.satellite.models import LinkState
from quasar.scenarios import WalkerDeltaConfig, WalkerDeltaLiteSource
from quasar.topology.engine import SpatiotemporalTopologyEngine
from quasar.topology.graph import TopologySnapshot


class QuasarExperimentRunner:
    """Compose existing QUASAR modules over explicit time points."""

    def __init__(self, config: ExperimentConfig = ExperimentConfig()) -> None:
        self.config = config

    def execute(self) -> ExperimentResult:
        """Execute a small explicit-time smoke experiment."""

        source_station, destination_station = houston_washington_pair(
            self.config.controlled_pair
        )
        source = self._scenario_source((source_station, destination_station))
        workload = FixedPairWorkload(source_station, destination_station)
        event_bridge = EventBridge()
        event_log = EventLog()
        edge_trace = EdgeTrace()
        path_trace = PathTrace()
        frames = []
        snapshots = []
        route_results = []
        snapshot_edge_counts = []
        previous_snapshot = None
        previous_route = None

        for time in self.config.time_points:
            frame = source.frame_at(time)
            snapshot = self._build_snapshot(frame)
            attributed_snapshot, edge_attributes = self._attribute_snapshot(snapshot)
            snapshot_edge_counts.append(
                self._snapshot_edge_count(attributed_snapshot)
            )
            request = workload.request_at(time)
            request.metadata.update(
                {
                    "edge_attributes": edge_attributes,
                    "swap_success_probability": self.config.baseline.zeta_swap,
                    "storage_delay_source": self._storage_delay_source(),
                }
            )
            route_result = self._route(attributed_snapshot, request, time)

            for attributes in edge_attributes:
                edge_trace.record(
                    time=time,
                    edge=attributes.endpoints,
                    attributes=attributes,
                    metadata={"storage_delay_source": self._storage_delay_source()},
                )
            path_trace.record(
                time=time,
                route_result=route_result,
                request=request,
                architecture=self.config.architecture,
                algorithm=self.config.routing_algorithm,
                metadata={"storage_delay_source": self._storage_delay_source()},
            )
            if previous_snapshot is not None:
                events = event_bridge.detect_events(
                    previous_state=previous_snapshot,
                    current_state=attributed_snapshot,
                    current_route=previous_route,
                    thresholds={
                        "channel_quality_threshold": self.config.baseline.eta0,
                        "fidelity_threshold": self.config.baseline.fidelity_threshold,
                    },
                )
                event_log.extend(events)

            frames.append(frame)
            snapshots.append(attributed_snapshot)
            route_results.append(route_result)
            previous_snapshot = attributed_snapshot
            previous_route = route_result

        summary = MetricSummary.from_logs(event_log, edge_trace, path_trace)
        total_candidate_edges = sum(
            item["candidate_edge_count"] for item in snapshot_edge_counts
        )
        total_available_edges = sum(
            item["available_edge_count"] for item in snapshot_edge_counts
        )
        topology_available_edge_ratio = 0.0
        if total_candidate_edges:
            topology_available_edge_ratio = (
                total_available_edges / total_candidate_edges
            )
        return ExperimentResult(
            config=self.config,
            frames=tuple(frames),
            snapshots=tuple(snapshots),
            route_results=tuple(route_results),
            event_log=event_log,
            edge_trace=edge_trace,
            path_trace=path_trace,
            summary=summary,
            metadata={
                "scenario_source": "WalkerDeltaLiteSource",
                "controlled_pair": (
                    source_station.name,
                    destination_station.name,
                ),
                "storage_delay_source": self._storage_delay_source(),
                "snapshot_edge_counts": tuple(snapshot_edge_counts),
                "total_candidate_edges": total_candidate_edges,
                "total_available_edges": total_available_edges,
                "topology_available_edge_ratio": topology_available_edge_ratio,
            },
        )

    def _scenario_source(self, ground_stations: Iterable) -> WalkerDeltaLiteSource:
        baseline = self.config.baseline
        return WalkerDeltaLiteSource(
            WalkerDeltaConfig(
                planes=self.config.planes,
                satellites_per_plane=self.config.satellites_per_plane,
                altitude_km=baseline.altitude_km,
                inclination_deg=baseline.inclination_deg,
                min_elevation_deg=baseline.min_elevation_deg,
                dt=baseline.dt,
                ground_stations=tuple(ground_stations),
                max_sgl_candidate_range_km=self.config.max_sgl_range_km,
                max_isl_candidate_range_km=self.config.max_isl_range_km,
            )
        )

    def _build_snapshot(self, frame) -> TopologySnapshot:
        engine = SpatiotemporalTopologyEngine(
            satellites=frame.satellites,
            ground_stations=frame.ground_stations,
            min_elevation_deg=self.config.baseline.min_elevation_deg,
            max_sgl_range_km=self.config.max_sgl_range_km,
            max_isl_range_km=self.config.max_isl_range_km,
        )
        return engine.build_snapshot(
            time=frame.time,
            candidate_links=frame.candidate_links,
        )

    def _attribute_snapshot(
        self,
        snapshot: TopologySnapshot,
    ) -> Tuple[TopologySnapshot, Tuple[EdgeAttributes, ...]]:
        attributed_edges = tuple(self._attribute_link(edge) for edge in snapshot.edges)
        attributed_snapshot = TopologySnapshot(
            time=snapshot.time,
            nodes=snapshot.nodes,
            edges=attributed_edges,
        )
        edge_attributes = tuple(
            self._edge_attributes(edge)
            for edge in attributed_snapshot.available_edges
        )
        return attributed_snapshot, edge_attributes

    def _snapshot_edge_count(self, snapshot: TopologySnapshot) -> dict:
        candidate_edge_count = len(snapshot.edges)
        available_edge_count = len(snapshot.available_edges)
        topology_available_edge_ratio = 0.0
        if candidate_edge_count:
            topology_available_edge_ratio = (
                available_edge_count / candidate_edge_count
            )
        return {
            "time": snapshot.time,
            "candidate_edge_count": candidate_edge_count,
            "available_edge_count": available_edge_count,
            "topology_available_edge_ratio": topology_available_edge_ratio,
        }

    def _attribute_link(self, edge: LinkState) -> LinkState:
        storage_delay = self._storage_delay(edge)
        metadata = {
            **edge.metadata,
            "storage_delay": storage_delay,
            "storage_delay_source": self._storage_delay_source(),
        }
        if not edge.available:
            return replace(edge, metadata=metadata)

        fidelity = fidelity_after_storage(
            delta_tau=storage_delay,
            f0=self.config.baseline.f0,
            tau_c=self.config.baseline.tau_c,
        )
        transmittance = self._transmittance(edge)
        return replace(
            edge,
            transmittance=transmittance,
            fidelity=fidelity,
            metadata=metadata,
        )

    def _edge_attributes(self, edge: LinkState) -> EdgeAttributes:
        storage_delay = edge.metadata.get("storage_delay", self._storage_delay(edge))
        transmittance = edge.transmittance
        if transmittance is None:
            transmittance = self._transmittance(edge)
        fidelity = edge.fidelity
        if fidelity is None:
            fidelity = fidelity_after_storage(
                delta_tau=storage_delay,
                f0=self.config.baseline.f0,
                tau_c=self.config.baseline.tau_c,
            )
        return EdgeAttributes(
            edge_type=edge.edge_type,
            endpoints=edge.endpoints,
            available=edge.available,
            transmittance=transmittance,
            success_probability=path_success_probability([transmittance]),
            distance_km=edge.distance_km,
            elevation_deg=edge.elevation_deg,
            storage_delay=storage_delay,
            fidelity=fidelity,
            updated_at=edge.updated_at,
        )

    def _route(self, snapshot: TopologySnapshot, request, time: float):
        if self.config.architecture == "sd":
            router = SDRouter()
        elif self.config.routing_algorithm == "dsp":
            router = OOSDSPRouter()
        elif self.config.routing_algorithm == "mpr":
            router = OOSMPRRouter()
        else:
            router = OOSEASRRouter(
                tau_c=self.config.baseline.tau_c,
                xi=self.config.workload.temporal_penalty_xi,
                initial_fidelity=self.config.baseline.f0,
                fidelity_threshold=self.config.baseline.fidelity_threshold,
                default_swap_success_probability=self.config.baseline.zeta_swap,
            )
        return router.compute_route(snapshot, request, time)

    def _transmittance(self, edge: LinkState) -> float:
        eta0 = edge.transmittance
        if eta0 is None:
            eta0 = self.config.baseline.eta0
        return total_transmittance(
            edge_type=edge.edge_type,
            eta0=eta0,
            kappa=self.config.baseline.kappa,
            elevation_deg=edge.elevation_deg,
            alpha=self.config.baseline.alpha,
            h0_km=self.config.baseline.h0_km,
        )

    def _storage_delay(self, edge: LinkState) -> float:
        if self.config.workload.storage_delay_policy == "synthetic_demo":
            return self.config.workload.synthetic_storage_delay
        return 0.0

    def _storage_delay_source(self) -> str:
        if self.config.workload.storage_delay_policy == "synthetic_demo":
            return "synthetic_demo_not_contact_schedule"
        return "zero_policy"
