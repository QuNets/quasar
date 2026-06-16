"""Deterministic QUASAR metrics-layer demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.channel.models import EdgeAttributes, EdgeType  # noqa: E402
from quasar.events import EventRecord, EventType  # noqa: E402
from quasar.metrics import EdgeTrace, EventLog, MetricSummary, PathTrace  # noqa: E402
from quasar.routing import RouteResult  # noqa: E402


def _format_float(value, digits=4, suffix=""):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}"


def _format_path(path):
    if not path:
        return "n/a"
    return " -> ".join(path)


def _print_event_log(event_log):
    print("EventLog")
    print(f"total events: {event_log.total_count}")
    print("event counts:")
    for event_type, count in sorted(
        event_log.count_by_type().items(),
        key=lambda item: item[0].value,
    ):
        print(f"  {event_type.value}: {count}")
    print()


def _print_edge_trace(edge_trace):
    print("EdgeTrace")
    print(f"available edge ratio:     {_format_float(edge_trace.available_edge_ratio())}")
    print(f"average transmittance:    {_format_float(edge_trace.average_transmittance())}")
    print(f"average success prob.:    {_format_float(edge_trace.average_success_probability())}")
    print(f"average fidelity:         {_format_float(edge_trace.average_fidelity())}")
    print()


def _print_path_trace(path_trace):
    print("PathTrace")
    print(f"path count:           {len(path_trace.records)}")
    print(f"routing success rate: {_format_float(path_trace.success_rate())}")
    print("records:")
    for index, record in enumerate(path_trace.records, start=1):
        print(f"  [{index}] {_format_path(record.path)}")
        print(f"      success:       {record.success}")
        print(f"      cost:          {_format_float(record.cost)}")
        print(f"      success prob.: {_format_float(record.success_probability)}")
        print(f"      fidelity:      {_format_float(record.fidelity)}")
    print()


def _print_summary(summary):
    data = summary.to_dict()
    print("MetricSummary")
    print(f"total_events:                {data['total_events']}")
    print("event_counts:")
    for event_type, count in sorted(data["event_counts"].items()):
        print(f"  {event_type}: {count}")
    print(f"available_edge_ratio:        {_format_float(data['available_edge_ratio'])}")
    print(f"average_transmittance:       {_format_float(data['average_transmittance'])}")
    print(f"average_success_probability: {_format_float(data['average_success_probability'])}")
    print(f"average_fidelity:            {_format_float(data['average_fidelity'])}")
    print(f"routing_success_rate:        {_format_float(data['routing_success_rate'])}")
    print(f"path_count:                  {data['path_count']}")
    print(f"edge_record_count:           {data['edge_record_count']}")
    print()


def _build_event_log():
    event_log = EventLog()
    event_log.extend(
        (
            EventRecord(EventType.LINK_DROP, time=0.1, endpoints=("SAT-1", "GS-A")),
            EventRecord(
                EventType.FIDELITY_LOSS,
                time=0.1,
                endpoints=("SAT-1", "GS-B"),
            ),
            EventRecord(EventType.GRAPH_UPDATE, time=0.1),
            EventRecord(EventType.ROUTE_RECOMPUTE, time=0.1),
            EventRecord(EventType.LINK_DROP, time=0.2, endpoints=("SAT-2", "GS-C")),
        )
    )
    return event_log


def _build_edge_trace():
    edge_trace = EdgeTrace()
    edge_trace.record(
        time=0.0,
        edge=("SAT-1", "GS-A"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-1", "GS-A"),
            available=True,
            transmittance=0.42,
            success_probability=0.38,
            fidelity=0.92,
        ),
    )
    edge_trace.record(
        time=0.0,
        edge=("SAT-1", "GS-B"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-1", "GS-B"),
            available=True,
            transmittance=0.36,
            success_probability=0.31,
            fidelity=0.86,
        ),
    )
    edge_trace.record(
        time=0.1,
        edge=("SAT-2", "GS-C"),
        attributes=EdgeAttributes(
            edge_type=EdgeType.SGL,
            endpoints=("SAT-2", "GS-C"),
            available=False,
            transmittance=0.18,
            success_probability=0.12,
            fidelity=0.70,
        ),
    )
    return edge_trace


def _build_path_trace():
    path_trace = PathTrace()
    path_trace.record(
        time=0.0,
        route_result=RouteResult(
            path=("GS-A", "SAT-1", "GS-B"),
            success=True,
            cost=1.2,
            success_probability=0.42,
            fidelity=0.86,
            storage_delay=0.02,
        ),
        algorithm="oos_easr",
    )
    path_trace.record(
        time=0.1,
        route_result=RouteResult(
            path=(),
            success=False,
            reason="route invalidated by link drop",
        ),
        algorithm="oos_easr",
    )
    return path_trace


def main() -> None:
    event_log = _build_event_log()
    edge_trace = _build_edge_trace()
    path_trace = _build_path_trace()
    summary = MetricSummary.from_logs(event_log, edge_trace, path_trace)

    print("# QUASAR metrics demo")
    print()
    print("This demo uses deterministic toy records to demonstrate QUASAR metrics collection.")
    print("It does not run a simulation loop or trigger route recomputation.")
    print()
    _print_event_log(event_log)
    _print_edge_trace(edge_trace)
    _print_path_trace(path_trace)
    _print_summary(summary)


if __name__ == "__main__":
    main()
