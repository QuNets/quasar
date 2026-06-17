"""Contact-window-age routing batch demo for QUASAR."""

from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.experiments import (  # noqa: E402
    ExperimentCase,
    WorkloadConfig,
    results_summary_rows,
    routing_baseline_cases,
    run_many,
)


def _format_float(value, digits=4):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _contact_delay_cases():
    cases = []
    for case in routing_baseline_cases():
        workload = WorkloadConfig(
            architecture="oos",
            routing_algorithm=case.config.routing_algorithm,
            storage_delay_policy="contact_window_age",
        )
        config = replace(case.config, workload=workload)
        cases.append(
            ExperimentCase(
                name=case.name,
                config=config,
                metadata={
                    **case.metadata,
                    "storage_delay_source": "sampled_contact_schedule_estimator",
                    "storage_delay_policy": "contact_window_age",
                },
            )
        )
    return tuple(cases)


def _print_table(rows):
    print(
        "case      router  attempts  successes  success_rate  topo_ratio  "
        "avg_delay  route_delay  avg_fidelity  events  storage_delay_source"
    )
    for row in rows:
        print(
            f"{row['case']:<9} "
            f"{row['routing_algorithm'].upper():<7} "
            f"{row['route_attempts']:>8} "
            f"{row['route_successes']:>10} "
            f"{_format_float(row['routing_success_rate']):>12} "
            f"{_format_float(row['topology_available_edge_ratio']):>10} "
            f"{_format_float(row['average_storage_delay']):>9} "
            f"{_format_float(row['average_route_storage_delay']):>11} "
            f"{_format_float(row['average_fidelity']):>13} "
            f"{row['total_events']:>6} "
            f"{row['storage_delay_source']}"
        )


def main() -> None:
    results = run_many(_contact_delay_cases())
    rows = results_summary_rows(results)

    print("# QUASAR contact-delay routing batch demo")
    print()
    print("This is a smoke-test batch, not full paper-scale evaluation.")
    print("WalkerDeltaLiteSource is simplified deterministic, not full TLE/SGP4.")
    print("storage delay is sampled contact-window-derived.")
    print("This is not full entanglement scheduling.")
    print("This is not resource reservation.")
    print("This is not queueing.")
    print()
    _print_table(rows)


if __name__ == "__main__":
    main()
