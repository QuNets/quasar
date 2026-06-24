"""Thin user-facing simulator facade for QUASAR single-step evaluations."""

from __future__ import annotations

from typing import Iterable, Optional, Union

from quasar.api.result import QuasarStepResult
from quasar.channel.loss import total_transmittance
from quasar.channel.models import ChannelParameters, EdgeAttributes
from quasar.channel.probability import path_success_probability
from quasar.memory.decoherence import fidelity_after_storage
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.topology.engine import SpatiotemporalTopologyEngine


class QuasarSimulator:
    """Small facade that composes topology, channel, and memory helpers.

    This class intentionally exposes only a single-step ``step`` method. It is
    not a full run loop, router, architecture model, or event scheduler.
    """

    def __init__(
        self,
        min_elevation_deg: float = 15.0,
        max_sgl_range_km: Optional[float] = None,
        max_isl_range_km: Optional[float] = None,
        channel_parameters: Optional[ChannelParameters] = None,
        initial_fidelity: float = 0.99,
        coherence_time: float = 0.1,
        default_storage_delay: float = 0.0,
    ) -> None:
        self.satellites = []
        self.ground_stations = []
        self.min_elevation_deg = min_elevation_deg
        self.max_sgl_range_km = max_sgl_range_km
        self.max_isl_range_km = max_isl_range_km
        self.channel_parameters = channel_parameters or ChannelParameters()
        self.initial_fidelity = initial_fidelity
        self.coherence_time = coherence_time
        self.default_storage_delay = default_storage_delay

    def add_satellite(self, satellite: Union[Satellite, str], **kwargs) -> Satellite:
        """Add a satellite model and return it."""

        if isinstance(satellite, Satellite):
            sat = satellite
        else:
            sat = Satellite(name=satellite, **kwargs)
        self.satellites.append(sat)
        return sat

    def add_ground_station(
        self,
        ground_station: Union[GroundStation, str],
        latitude_deg: Optional[float] = None,
        longitude_deg: Optional[float] = None,
        **kwargs,
    ) -> GroundStation:
        """Add a ground station model and return it."""

        if isinstance(ground_station, GroundStation):
            station = ground_station
        else:
            if latitude_deg is None:
                raise ValueError("latitude_deg is required when using a ground-station name")
            if longitude_deg is None:
                raise ValueError("longitude_deg is required when using a ground-station name")
            station = GroundStation(
                name=ground_station,
                latitude_deg=latitude_deg,
                longitude_deg=longitude_deg,
                **kwargs,
            )
        self.ground_stations.append(station)
        return station

    def step(self, time: float, candidate_links: Iterable[LinkState]) -> QuasarStepResult:
        """Build G(t), attach channel/memory attributes, and return a result."""

        snapshot = self._topology_engine().build_snapshot(time=time, candidate_links=candidate_links)
        edge_attributes = tuple(self._build_edge_attributes(edge) for edge in snapshot.available_edges)
        return QuasarStepResult(
            time=time,
            snapshot=snapshot,
            edge_attributes=edge_attributes,
        )

    def _topology_engine(self) -> SpatiotemporalTopologyEngine:
        return SpatiotemporalTopologyEngine(
            satellites=self.satellites,
            ground_stations=self.ground_stations,
            min_elevation_deg=self.min_elevation_deg,
            max_sgl_range_km=self.max_sgl_range_km,
            max_isl_range_km=self.max_isl_range_km,
        )

    def _build_edge_attributes(self, edge: LinkState) -> EdgeAttributes:
        transmittance = self._edge_transmittance(edge)
        storage_delay = self._storage_delay(edge)
        fidelity = fidelity_after_storage(
            delta_tau=storage_delay,
            f0=edge.fidelity if edge.fidelity is not None else self.initial_fidelity,
            tau_c=self.coherence_time,
        )
        success_probability = path_success_probability([transmittance])
        return EdgeAttributes(
            edge_type=edge.edge_type,
            endpoints=edge.endpoints,
            available=edge.available,
            transmittance=transmittance,
            success_probability=success_probability,
            distance_km=edge.distance_km,
            elevation_deg=edge.elevation_deg,
            storage_delay=storage_delay,
            fidelity=fidelity,
            updated_at=edge.updated_at,
        )

    def _edge_transmittance(self, edge: LinkState) -> float:
        eta0 = edge.transmittance
        if eta0 is None:
            eta0 = self.channel_parameters.base_transmittance
        return total_transmittance(
            edge_type=edge.edge_type,
            eta0=eta0,
            kappa=self.channel_parameters.implementation_efficiency,
            elevation_deg=edge.elevation_deg,
            alpha=self.channel_parameters.atmospheric_attenuation,
            h0_km=self.channel_parameters.atmosphere_thickness_km,
        )

    def _storage_delay(self, edge: LinkState) -> float:
        storage_delay = edge.metadata.get("storage_delay", self.default_storage_delay)
        if storage_delay < 0:
            raise ValueError("storage_delay must be non-negative")
        return storage_delay
