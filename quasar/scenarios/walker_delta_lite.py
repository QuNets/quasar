"""Deterministic Walker-Delta-lite candidate link source.

WalkerDeltaLiteSource uses a simplified circular geometry model for repeatable
tests and demos. It is not full TLE/SGP4 propagation and should not be treated
as an orbital-accuracy model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, degrees, pi, radians, sin, sqrt
from typing import Any, Dict, Iterable, Optional, Tuple

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.scenarios.base import ScenarioFrame


Vector3 = Tuple[float, float, float]


@dataclass(frozen=True)
class WalkerDeltaConfig:
    """Configuration for the deterministic Walker-Delta-lite source."""

    planes: int
    satellites_per_plane: int
    altitude_km: float = 500.0
    inclination_deg: float = 53.0
    earth_radius_km: float = 6371.0
    min_elevation_deg: float = 15.0
    dt: float = 0.1
    ground_stations: Iterable[GroundStation] = field(default_factory=tuple)
    epoch: float = 0.0
    angular_rate_deg_per_s: Optional[float] = None
    max_sgl_candidate_range_km: Optional[float] = None
    max_isl_candidate_range_km: Optional[float] = None
    include_sgl: bool = True
    include_isl: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.planes <= 0:
            raise ValueError("planes must be positive")
        if self.satellites_per_plane <= 0:
            raise ValueError("satellites_per_plane must be positive")
        if self.altitude_km < 0:
            raise ValueError("altitude_km must be non-negative")
        if not 0.0 <= self.inclination_deg <= 180.0:
            raise ValueError("inclination_deg must be in [0, 180]")
        if self.earth_radius_km <= 0:
            raise ValueError("earth_radius_km must be positive")
        if not 0.0 <= self.min_elevation_deg <= 90.0:
            raise ValueError("min_elevation_deg must be in [0, 90]")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.epoch < 0:
            raise ValueError("epoch must be non-negative")
        if self.angular_rate_deg_per_s is not None and self.angular_rate_deg_per_s < 0:
            raise ValueError("angular_rate_deg_per_s must be non-negative")
        for field_name, value in (
            ("max_sgl_candidate_range_km", self.max_sgl_candidate_range_km),
            ("max_isl_candidate_range_km", self.max_isl_candidate_range_km),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        object.__setattr__(self, "ground_stations", tuple(self.ground_stations))


class WalkerDeltaLiteSource:
    """Generate deterministic Walker-Delta-style candidate links."""

    def __init__(self, config: WalkerDeltaConfig) -> None:
        self.config = config
        self.satellites = self._build_satellites()

    def frame_at(self, time: float) -> ScenarioFrame:
        """Return generated candidate links for a simulation time."""

        if time < 0:
            raise ValueError("time must be non-negative")
        positions = self.satellite_positions_at(time)
        candidate_links = []
        if self.config.include_sgl:
            candidate_links.extend(self._sgl_candidate_links(time, positions))
        if self.config.include_isl:
            candidate_links.extend(self._isl_candidate_links(time, positions))
        metadata = {
            **self.config.metadata,
            "source": "walker_delta_lite",
            "model": "simplified deterministic circular geometry",
            "satellite_positions": positions,
            "storage_delay_source": "not_provided",
        }
        return ScenarioFrame(
            time=time,
            satellites=self.satellites,
            ground_stations=self.config.ground_stations,
            candidate_links=tuple(candidate_links),
            metadata=metadata,
        )

    def candidate_links_at(self, time: float) -> Tuple[LinkState, ...]:
        """Return candidate links for a simulation time."""

        return self.frame_at(time).candidate_links

    def satellite_positions_at(self, time: float) -> Dict[str, Vector3]:
        """Return simplified satellite positions keyed by satellite name."""

        return {
            satellite.name: self._satellite_position(satellite, time)
            for satellite in self.satellites
        }

    def _build_satellites(self) -> Tuple[Satellite, ...]:
        satellites = []
        for plane in range(self.config.planes):
            for slot in range(self.config.satellites_per_plane):
                satellites.append(
                    Satellite(
                        name=f"SAT-P{plane}-S{slot}",
                        altitude_km=self.config.altitude_km,
                        inclination_deg=self.config.inclination_deg,
                        orbit_plane=plane,
                        slot=slot,
                        metadata={"source": "walker_delta_lite"},
                    )
                )
        return tuple(satellites)

    def _satellite_position(self, satellite: Satellite, time: float) -> Vector3:
        radius = self.config.earth_radius_km + self.config.altitude_km
        plane = satellite.orbit_plane or 0
        slot = satellite.slot or 0
        plane_count = self.config.planes
        slot_count = self.config.satellites_per_plane
        angular_rate = self.config.angular_rate_deg_per_s
        if angular_rate is None:
            angular_rate = 360.0 / 5400.0

        raan = 2.0 * pi * plane / plane_count
        phase = 2.0 * pi * (slot / slot_count + plane / (plane_count * slot_count))
        phase += radians(angular_rate * (time - self.config.epoch))
        inclination = radians(self.config.inclination_deg)

        x_orbit = radius * cos(phase)
        y_orbit = radius * sin(phase)
        x_inclined = x_orbit
        y_inclined = y_orbit * cos(inclination)
        z_inclined = y_orbit * sin(inclination)

        x = x_inclined * cos(raan) - y_inclined * sin(raan)
        y = x_inclined * sin(raan) + y_inclined * cos(raan)
        return (x, y, z_inclined)

    def _sgl_candidate_links(
        self,
        time: float,
        positions: Dict[str, Vector3],
    ) -> Tuple[LinkState, ...]:
        links = []
        for satellite in self.satellites:
            satellite_position = positions[satellite.name]
            for station in self.config.ground_stations:
                station_position = _ground_position(station, self.config.earth_radius_km)
                distance = _distance(satellite_position, station_position)
                if not _within_optional_range(distance, self.config.max_sgl_candidate_range_km):
                    continue
                elevation = _elevation_deg(satellite_position, station_position)
                links.append(
                    LinkState(
                        endpoints=(satellite.name, station.name),
                        edge_type=EdgeType.SGL,
                        distance_km=distance,
                        elevation_deg=elevation,
                        updated_at=time,
                        metadata={
                            "source": "walker_delta_lite",
                            "storage_delay_source": "not_provided",
                        },
                    )
                )
        return tuple(links)

    def _isl_candidate_links(
        self,
        time: float,
        positions: Dict[str, Vector3],
    ) -> Tuple[LinkState, ...]:
        links = []
        for first, second in self._isl_pairs():
            distance = _distance(positions[first.name], positions[second.name])
            if not _within_optional_range(distance, self.config.max_isl_candidate_range_km):
                continue
            links.append(
                LinkState(
                    endpoints=(first.name, second.name),
                    edge_type=EdgeType.ISL,
                    distance_km=distance,
                    elevation_deg=None,
                    updated_at=time,
                    metadata={
                        "source": "walker_delta_lite",
                        "storage_delay_source": "not_provided",
                    },
                )
            )
        return tuple(links)

    def _isl_pairs(self) -> Tuple[Tuple[Satellite, Satellite], ...]:
        by_index = {
            (satellite.orbit_plane, satellite.slot): satellite
            for satellite in self.satellites
        }
        pairs = {}
        for plane in range(self.config.planes):
            for slot in range(self.config.satellites_per_plane):
                current = by_index[(plane, slot)]
                if self.config.satellites_per_plane > 1:
                    neighbor = by_index[
                        (plane, (slot + 1) % self.config.satellites_per_plane)
                    ]
                    pair = _satellite_pair(current, neighbor)
                    pairs[(pair[0].name, pair[1].name)] = pair
                if self.config.planes > 1:
                    neighbor = by_index[((plane + 1) % self.config.planes, slot)]
                    pair = _satellite_pair(current, neighbor)
                    pairs[(pair[0].name, pair[1].name)] = pair
        return tuple(
            pair
            for _, pair in sorted(pairs.items(), key=lambda item: item[0])
        )


def _satellite_pair(first: Satellite, second: Satellite) -> Tuple[Satellite, Satellite]:
    if first.name < second.name:
        return first, second
    return second, first


def _ground_position(station: GroundStation, earth_radius_km: float) -> Vector3:
    radius = earth_radius_km + station.altitude_km
    latitude = radians(station.latitude_deg)
    longitude = radians(station.longitude_deg)
    x = radius * cos(latitude) * cos(longitude)
    y = radius * cos(latitude) * sin(longitude)
    z = radius * sin(latitude)
    return (x, y, z)


def _distance(first: Vector3, second: Vector3) -> float:
    return sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def _elevation_deg(satellite_position: Vector3, station_position: Vector3) -> float:
    line = tuple(a - b for a, b in zip(satellite_position, station_position))
    line_norm = _norm(line)
    station_norm = _norm(station_position)
    if line_norm == 0 or station_norm == 0:
        return -90.0
    projection = sum(a * b for a, b in zip(line, station_position))
    sine_elevation = projection / (line_norm * station_norm)
    sine_elevation = max(-1.0, min(1.0, sine_elevation))
    return degrees(asin(sine_elevation))


def _norm(vector: Vector3) -> float:
    return sqrt(sum(value * value for value in vector))


def _within_optional_range(distance_km: float, max_range_km: Optional[float]) -> bool:
    return max_range_km is None or distance_km <= max_range_km
