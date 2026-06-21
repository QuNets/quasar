"""Trace-driven TLE/SGP4 scenario source for QUASAR.

This source turns a small TLE trace into time-indexed satellite positions and
candidate ``LinkState`` objects. SGP4 is used only as the orbital input layer;
visibility and range pruning remain in the topology engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, radians, sin, sqrt
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Tuple

from quasar.channel.models import EdgeType
from quasar.satellite.models import GroundStation, LinkState, Satellite
from quasar.scenarios.base import ScenarioFrame

try:
    from sgp4.api import Satrec
except ImportError:  # pragma: no cover - exercised through monkeypatch tests
    Satrec = None


Vector3 = Tuple[float, float, float]


@dataclass(frozen=True)
class _TLEEntry:
    name: str
    line1: str
    line2: str


class TLESGP4Source:
    """Generate candidate links from a small TLE trace using SGP4.

    The source exposes the same ``frame_at`` / ``candidate_links_at`` interface
    as other QUASAR scenario sources. It is intended for trace-driven topology
    experiments and does not implement paper-scale evaluation, resource
    scheduling, or heavy astronomy coordinate stacks.
    """

    def __init__(
        self,
        tle_lines: Iterable[str] = (),
        ground_stations: Iterable[GroundStation] = (),
        tle_path: Optional[Path | str] = None,
        earth_radius_km: float = 6371.0,
        include_sgl: bool = True,
        include_isl: bool = False,
        max_sgl_candidate_range_km: Optional[float] = None,
        max_isl_candidate_range_km: Optional[float] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> None:
        if earth_radius_km <= 0:
            raise ValueError("earth_radius_km must be positive")
        for field_name, value in (
            ("max_sgl_candidate_range_km", max_sgl_candidate_range_km),
            ("max_isl_candidate_range_km", max_isl_candidate_range_km),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

        raw_lines = tuple(tle_lines)
        if tle_path is not None:
            raw_lines = _read_tle_file(tle_path)
        self.tle_entries = _parse_tle_entries(raw_lines)
        self.ground_stations = tuple(ground_stations)
        self.earth_radius_km = earth_radius_km
        self.include_sgl = include_sgl
        self.include_isl = include_isl
        self.max_sgl_candidate_range_km = max_sgl_candidate_range_km
        self.max_isl_candidate_range_km = max_isl_candidate_range_km
        self.metadata = dict(metadata or {})
        self.satellites = tuple(
            Satellite(
                name=entry.name,
                metadata={
                    "source": "tle_sgp4",
                    "tle_line1": entry.line1,
                    "tle_line2": entry.line2,
                },
            )
            for entry in self.tle_entries
        )
        self._satrec_by_name: Optional[Dict[str, object]] = None

    @classmethod
    def from_file(
        cls,
        tle_path: Path | str,
        ground_stations: Iterable[GroundStation] = (),
        **kwargs,
    ) -> "TLESGP4Source":
        """Create a source from a local TLE file."""

        return cls(tle_path=tle_path, ground_stations=ground_stations, **kwargs)

    def frame_at(self, time: float) -> ScenarioFrame:
        """Return a scenario frame for ``time`` seconds after each TLE epoch."""

        if time < 0:
            raise ValueError("time must be non-negative")
        positions = self.satellite_positions_at(time)
        subpoints = self.satellite_subpoints_at(time, positions)
        candidate_links = []
        if self.include_sgl:
            candidate_links.extend(self._sgl_candidate_links(time, positions))
        if self.include_isl:
            candidate_links.extend(self._isl_candidate_links(time, positions))

        metadata = {
            **self.metadata,
            "source": "tle_sgp4",
            "model": "trace-driven SGP4 propagation",
            "satellite_positions": positions,
            "satellite_subpoints": subpoints,
            "storage_delay_source": "not_provided",
        }
        return ScenarioFrame(
            time=time,
            satellites=self.satellites,
            ground_stations=self.ground_stations,
            candidate_links=tuple(candidate_links),
            metadata=metadata,
        )

    def candidate_links_at(self, time: float) -> Tuple[LinkState, ...]:
        """Return candidate links for a simulation time."""

        return self.frame_at(time).candidate_links

    def satellite_positions_at(self, time: float) -> Dict[str, Vector3]:
        """Return SGP4 TEME-like positions in kilometers by satellite name."""

        if time < 0:
            raise ValueError("time must be non-negative")
        records = self._satrec_records()
        positions = {}
        for entry in self.tle_entries:
            record = records[entry.name]
            jd = record.jdsatepoch
            fr = record.jdsatepochF + time / 86400.0
            error, position, _ = record.sgp4(jd, fr)
            if error != 0:
                raise ValueError(
                    f"SGP4 propagation failed for {entry.name} with error {error}"
                )
            positions[entry.name] = tuple(float(value) for value in position)
        return positions

    def satellite_subpoints_at(
        self,
        time: float,
        positions: Optional[Mapping[str, Vector3]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Return approximate geodetic subpoints for propagated positions."""

        if positions is None:
            positions = self.satellite_positions_at(time)
        records = self._satrec_records()
        subpoints = {}
        for entry in self.tle_entries:
            record = records[entry.name]
            jd = record.jdsatepoch
            fr = record.jdsatepochF + time / 86400.0
            latitude, longitude, altitude = _subpoint_from_eci(
                positions[entry.name],
                jd + fr,
                self.earth_radius_km,
            )
            subpoints[entry.name] = {
                "latitude_deg": latitude,
                "longitude_deg": longitude,
                "altitude_km": altitude,
            }
        return subpoints

    def _satrec_records(self) -> Dict[str, object]:
        self._require_sgp4()
        if self._satrec_by_name is None:
            self._satrec_by_name = {
                entry.name: Satrec.twoline2rv(entry.line1, entry.line2)
                for entry in self.tle_entries
            }
        return self._satrec_by_name

    def _sgl_candidate_links(
        self,
        time: float,
        positions: Mapping[str, Vector3],
    ) -> Tuple[LinkState, ...]:
        links = []
        records = self._satrec_records()
        for satellite in self.satellites:
            satellite_position = positions[satellite.name]
            record = records[satellite.name]
            jd = record.jdsatepoch
            fr = record.jdsatepochF + time / 86400.0
            for station in self.ground_stations:
                station_position = _ground_position_eci(
                    station,
                    jd + fr,
                    self.earth_radius_km,
                )
                distance = _distance(satellite_position, station_position)
                if not _within_optional_range(
                    distance,
                    self.max_sgl_candidate_range_km,
                ):
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
                            "source": "tle_sgp4",
                            "storage_delay_source": "not_provided",
                        },
                    )
                )
        return tuple(links)

    def _isl_candidate_links(
        self,
        time: float,
        positions: Mapping[str, Vector3],
    ) -> Tuple[LinkState, ...]:
        links = []
        for first, second in _adjacent_satellite_pairs(self.satellites):
            distance = _distance(positions[first.name], positions[second.name])
            if not _within_optional_range(
                distance,
                self.max_isl_candidate_range_km,
            ):
                continue
            links.append(
                LinkState(
                    endpoints=(first.name, second.name),
                    edge_type=EdgeType.ISL,
                    distance_km=distance,
                    elevation_deg=None,
                    updated_at=time,
                    metadata={
                        "source": "tle_sgp4",
                        "storage_delay_source": "not_provided",
                    },
                )
            )
        return tuple(links)

    @staticmethod
    def _require_sgp4() -> None:
        if Satrec is None:
            raise ImportError(
                "TLESGP4Source requires the optional 'sgp4' package. "
                "Install sgp4 to use TLE-based propagation."
            )


def _read_tle_file(tle_path: Path | str) -> Tuple[str, ...]:
    path = Path(tle_path)
    return tuple(path.read_text(encoding="utf-8").splitlines())


def _parse_tle_entries(lines: Iterable[str]) -> Tuple[_TLEEntry, ...]:
    cleaned = tuple(line.strip() for line in lines if line.strip())
    entries = []
    index = 0
    while index < len(cleaned):
        if cleaned[index].startswith("1 "):
            name = _default_tle_name(cleaned[index])
            line1 = cleaned[index]
            index += 1
        else:
            name = cleaned[index]
            index += 1
            if index >= len(cleaned):
                raise ValueError(f"missing TLE line 1 for {name!r}")
            line1 = cleaned[index]
            index += 1
        if index >= len(cleaned):
            raise ValueError(f"missing TLE line 2 for {name!r}")
        line2 = cleaned[index]
        index += 1
        if not line1.startswith("1 ") or not line2.startswith("2 "):
            raise ValueError(f"invalid TLE record for {name!r}")
        entries.append(_TLEEntry(name=name, line1=line1, line2=line2))
    return tuple(entries)


def _default_tle_name(line1: str) -> str:
    satellite_number = line1[2:7].strip() or "UNKNOWN"
    return f"TLE-{satellite_number}"


def _adjacent_satellite_pairs(
    satellites: Tuple[Satellite, ...],
) -> Tuple[Tuple[Satellite, Satellite], ...]:
    if len(satellites) < 2:
        return ()
    pairs = []
    for index in range(len(satellites) - 1):
        pairs.append((satellites[index], satellites[index + 1]))
    return tuple(pairs)


def _ground_position_eci(
    station: GroundStation,
    julian_date: float,
    earth_radius_km: float,
) -> Vector3:
    ecef = _ground_position_ecef(station, earth_radius_km)
    theta = _gmst_radians(julian_date)
    x, y, z = ecef
    return (
        cos(theta) * x - sin(theta) * y,
        sin(theta) * x + cos(theta) * y,
        z,
    )


def _ground_position_ecef(
    station: GroundStation,
    earth_radius_km: float,
) -> Vector3:
    radius = earth_radius_km + station.altitude_km
    latitude = radians(station.latitude_deg)
    longitude = radians(station.longitude_deg)
    x = radius * cos(latitude) * cos(longitude)
    y = radius * cos(latitude) * sin(longitude)
    z = radius * sin(latitude)
    return (x, y, z)


def _subpoint_from_eci(
    position: Vector3,
    julian_date: float,
    earth_radius_km: float,
) -> Tuple[float, float, float]:
    theta = _gmst_radians(julian_date)
    x_eci, y_eci, z = position
    x = cos(theta) * x_eci + sin(theta) * y_eci
    y = -sin(theta) * x_eci + cos(theta) * y_eci
    radius_xy = sqrt(x * x + y * y)
    radius = sqrt(radius_xy * radius_xy + z * z)
    latitude = degrees(atan2(z, radius_xy))
    longitude = _normalize_longitude(degrees(atan2(y, x)))
    altitude = radius - earth_radius_km
    return latitude, longitude, altitude


def _gmst_radians(julian_date: float) -> float:
    centuries = (julian_date - 2451545.0) / 36525.0
    gmst_deg = (
        280.46061837
        + 360.98564736629 * (julian_date - 2451545.0)
        + 0.000387933 * centuries * centuries
        - centuries * centuries * centuries / 38710000.0
    )
    return radians(gmst_deg % 360.0)


def _normalize_longitude(longitude: float) -> float:
    while longitude > 180.0:
        longitude -= 360.0
    while longitude < -180.0:
        longitude += 360.0
    return longitude


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
