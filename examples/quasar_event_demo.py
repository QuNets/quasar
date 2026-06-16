"""Deterministic QUASAR event-bridge demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.channel.models import EdgeType  # noqa: E402
from quasar.events import EventBridge  # noqa: E402
from quasar.satellite.models import LinkState  # noqa: E402
from quasar.topology.graph import TopologySnapshot  # noqa: E402


def _format_value(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    if _is_edge_tuple_list(value):
        return "; ".join(_format_endpoints(item) for item in value)
    if isinstance(value, tuple):
        return ", ".join(_format_value(item) for item in value)
    return str(value)


def _is_edge_tuple_list(value):
    return (
        isinstance(value, tuple)
        and value
        and all(isinstance(item, tuple) and len(item) == 2 for item in value)
    )


def _format_endpoints(endpoints):
    if endpoints is None:
        return "n/a"
    first, second = endpoints
    return f"{first} <-> {second}"


def _print_event_record(index, record):
    print(f"[{index}] {record.event_type.value}")
    print(f"edge:       {_format_endpoints(record.endpoints)}")
    print(f"time:       {record.time:.3f} s")
    print(f"previous:   {_format_value(record.previous_value)}")
    print(f"current:    {_format_value(record.current_value)}")
    print(f"threshold:  {_format_value(record.threshold)}")
    print(f"reason:     {_format_value(record.reason)}")
    if record.metadata:
        print(f"metadata:   {_format_value(tuple(record.metadata.keys()))}")
    print()


def _build_previous_state():
    return TopologySnapshot(
        time=0.0,
        nodes=("GS-A", "GS-B", "SAT-1"),
        edges=(
            LinkState(
                endpoints=("GS-A", "SAT-1"),
                edge_type=EdgeType.SGL,
                available=True,
                transmittance=0.80,
                fidelity=0.86,
            ),
            LinkState(
                endpoints=("SAT-1", "GS-B"),
                edge_type=EdgeType.SGL,
                available=True,
                transmittance=0.75,
                fidelity=0.82,
            ),
        ),
    )


def _build_current_state():
    return TopologySnapshot(
        time=0.1,
        nodes=("GS-A", "GS-B", "SAT-1"),
        edges=(
            LinkState(
                endpoints=("GS-A", "SAT-1"),
                edge_type=EdgeType.SGL,
                available=False,
                transmittance=0.80,
                fidelity=0.86,
            ),
            LinkState(
                endpoints=("SAT-1", "GS-B"),
                edge_type=EdgeType.SGL,
                available=True,
                transmittance=0.75,
                fidelity=0.70,
            ),
        ),
    )


def main() -> None:
    previous_state = _build_previous_state()
    current_state = _build_current_state()
    current_route = ("GS-A", "SAT-1", "GS-B")

    records = EventBridge().detect_events(
        previous_state=previous_state,
        current_state=current_state,
        current_route=current_route,
        thresholds={
            "channel_quality_threshold": 0.50,
            "fidelity_threshold": 0.75,
        },
    )

    print("# QUASAR event demo")
    print()
    print("Deterministic previous/current state comparison.")
    print("Delta t = 100 ms is a state-check interval only.")
    print("No full recomputation loop or route recomputation is executed.")
    print()
    print("Current route under observation:")
    print("GS-A -> SAT-1 -> GS-B")
    print()
    print("Detected EventRecord objects:")
    print()
    for index, record in enumerate(records, start=1):
        _print_event_record(index, record)


if __name__ == "__main__":
    main()
