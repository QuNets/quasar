"""Deterministic QUASAR scenario-source demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.channel.models import EdgeType  # noqa: E402
from quasar.satellite.models import GroundStation  # noqa: E402
from quasar.scenarios import WalkerDeltaConfig, WalkerDeltaLiteSource  # noqa: E402
from quasar.topology.engine import SpatiotemporalTopologyEngine  # noqa: E402


def _count_edges(candidate_links, edge_type):
    return sum(1 for link in candidate_links if link.edge_type == edge_type)


def main() -> None:
    ground_stations = (
        GroundStation("GS-A", latitude_deg=0.0, longitude_deg=0.0),
        GroundStation("GS-B", latitude_deg=35.0, longitude_deg=120.0),
    )
    source = WalkerDeltaLiteSource(
        WalkerDeltaConfig(
            planes=2,
            satellites_per_plane=3,
            ground_stations=ground_stations,
            max_sgl_candidate_range_km=None,
            max_isl_candidate_range_km=None,
        )
    )
    frame = source.frame_at(0.0)
    engine = SpatiotemporalTopologyEngine(
        satellites=frame.satellites,
        ground_stations=frame.ground_stations,
        min_elevation_deg=15.0,
        max_sgl_range_km=2500.0,
        max_isl_range_km=8000.0,
    )
    snapshot = engine.build_snapshot(
        time=frame.time,
        candidate_links=frame.candidate_links,
    )

    print("# QUASAR scenario demo")
    print()
    print("WalkerDeltaLiteSource is a simplified deterministic")
    print("Walker-Delta-style source, not full TLE/SGP4 propagation.")
    print("storage_delay is not provided by this source.")
    print()
    print(f"Scenario source type: {source.__class__.__name__}")
    print(f"time: {frame.time:.3f} s")
    print(f"satellites: {len(frame.satellites)}")
    print(f"ground stations: {len(frame.ground_stations)}")
    print(f"candidate links: {len(frame.candidate_links)}")
    print(f"SGL candidates: {_count_edges(frame.candidate_links, EdgeType.SGL)}")
    print(f"ISL candidates: {_count_edges(frame.candidate_links, EdgeType.ISL)}")
    print()
    print("Topology snapshot after visibility/range pruning:")
    print(f"node count: {snapshot.node_count}")
    print(f"total edge count: {len(snapshot.edges)}")
    print(f"available edge count: {len(snapshot.available_edges)}")


if __name__ == "__main__":
    main()
