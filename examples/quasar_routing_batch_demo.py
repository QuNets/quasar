"""Routing baseline batch demo for QUASAR smoke experiments."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.experiments import (  # noqa: E402
    results_summary_rows,
    routing_baseline_cases,
    run_many,
)


def _format_float(value, digits=4):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _print_table(rows):
    print(
        "case      arch  router  attempts  successes  "
        "success_rate  topo_ratio  avg_eta  avg_fidelity  events"
    )
    for row in rows:
        print(
            f"{row['case']:<9} "
            f"{row['architecture'].upper():<5} "
            f"{row['routing_algorithm'].upper():<7} "
            f"{row['route_attempts']:>8} "
            f"{row['route_successes']:>10} "
            f"{_format_float(row['routing_success_rate']):>12} "
            f"{_format_float(row['topology_available_edge_ratio']):>10} "
            f"{_format_float(row['average_transmittance']):>8} "
            f"{_format_float(row['average_fidelity']):>13} "
            f"{row['total_events']:>6}"
        )


def main() -> None:
    cases = routing_baseline_cases()
    results = run_many(cases)
    rows = results_summary_rows(results)

    print("# QUASAR routing baseline batch demo")
    print()
    print("This is a smoke-test batch, not full paper-scale evaluation.")
    print("This is not 24h evaluation.")
    print("WalkerDeltaLiteSource is simplified deterministic, not full TLE/SGP4.")
    print("storage_delay is zero_policy, not contact-schedule-derived.")
    print()
    _print_table(rows)


if __name__ == "__main__":
    main()
