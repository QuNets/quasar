"""Trace-driven TLE/SGP4 scenario-source demo for QUASAR."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.channel.models import EdgeType  # noqa: E402
from quasar.satellite.models import GroundStation  # noqa: E402
from quasar.scenarios import TLESGP4Source  # noqa: E402
from quasar.topology.engine import SpatiotemporalTopologyEngine  # noqa: E402


TIME_POINTS = (0.0, 300.0, 600.0)


def _count_edges(candidate_links, edge_type):
    return sum(1 for link in candidate_links if link.edge_type == edge_type)


def _format_float(value, digits=3):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _demo_ground_station(tle_path):
    seed_source = TLESGP4Source.from_file(tle_path)
    seed_frame = seed_source.frame_at(TIME_POINTS[0])
    first_satellite = seed_frame.satellites[0].name
    subpoint = seed_frame.metadata["satellite_subpoints"][first_satellite]
    return GroundStation(
        "TRACE-GS",
        latitude_deg=subpoint["latitude_deg"],
        longitude_deg=subpoint["longitude_deg"],
    )


def main() -> None:
    tle_path = Path(__file__).resolve().parent / "data" / "tle_sample.tle"
    ground_station = _demo_ground_station(tle_path)
    source = TLESGP4Source.from_file(
        tle_path,
        ground_stations=(ground_station,),
        include_isl=True,
    )

    print("# QUASAR TLE trace demo")
    print()
    print("This demo uses a small public fixture, not a private Starlink trace.")
    print("TLESGP4Source uses SGP4 as a trace-driven orbital input source.")
    print("Visibility and range pruning are still handled by the topology engine.")
    print("This is not a 24h paper-scale evaluation.")
    print()
    print(f"TLE file: {tle_path.name}")
    print(f"ground station: {ground_station.name}")
    print(
        "ground station lat/lon: "
        f"{_format_float(ground_station.latitude_deg)}, "
        f"{_format_float(ground_station.longitude_deg)}"
    )
    print()
    print(
        "time(s)  satellites  GS  candidates  SGL  ISL  visible_SGL  "
        "available_edges"
    )

    for time in TIME_POINTS:
        frame = source.frame_at(time)
        engine = SpatiotemporalTopologyEngine(
            satellites=frame.satellites,
            ground_stations=frame.ground_stations,
            min_elevation_deg=0.0,
            max_sgl_range_km=None,
            max_isl_range_km=None,
        )
        snapshot = engine.build_snapshot(
            time=frame.time,
            candidate_links=frame.candidate_links,
        )
        visible_sgl_count = _count_edges(snapshot.available_edges, EdgeType.SGL)
        print(
            f"{time:7.1f}  "
            f"{len(frame.satellites):10d}  "
            f"{len(frame.ground_stations):2d}  "
            f"{len(frame.candidate_links):10d}  "
            f"{_count_edges(frame.candidate_links, EdgeType.SGL):3d}  "
            f"{_count_edges(frame.candidate_links, EdgeType.ISL):3d}  "
            f"{visible_sgl_count:11d}  "
            f"{len(snapshot.available_edges):15d}"
        )


if __name__ == "__main__":
    main()
