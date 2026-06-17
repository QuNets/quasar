"""Storage-delay diagnostics demo for QUASAR smoke experiments."""

from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.experiments import (  # noqa: E402
    ExperimentCase,
    WorkloadConfig,
    results_summary_rows,
    route_diagnostic_rows,
    routing_baseline_cases,
    run_many,
)


def _format_float(value, digits=4):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _cases_for_policy(policy):
    cases = []
    for case in routing_baseline_cases():
        workload = WorkloadConfig(
            architecture="oos",
            routing_algorithm=case.config.routing_algorithm,
            storage_delay_policy=policy,
        )
        config = replace(case.config, workload=workload)
        cases.append(
            ExperimentCase(
                name=case.name,
                config=config,
                metadata={**case.metadata, "storage_delay_policy": policy},
            )
        )
    return tuple(cases)


def _print_summary_table(title, rows):
    print(title)
    print(
        "router  attempts  successes  success_rate  avg_edge_delay  "
        "avg_route_delay  avg_route_fidelity  events"
    )
    for row in rows:
        print(
            f"{row['routing_algorithm'].upper():<7} "
            f"{row['route_attempts']:>8} "
            f"{row['route_successes']:>10} "
            f"{_format_float(row['routing_success_rate']):>12} "
            f"{_format_float(row['average_edge_storage_delay']):>14} "
            f"{_format_float(row['average_route_storage_delay']):>15} "
            f"{_format_float(row['average_route_fidelity']):>18} "
            f"{row['total_events']:>6}"
        )
    print()


def _print_route_diagnostics(title, results, limit=3):
    print(title)
    for result in results:
        router = result.config.routing_algorithm.upper()
        print(f"{router}:")
        rows = route_diagnostic_rows(result)
        for row in rows[:limit]:
            path = " -> ".join(row["selected_path"]) or "n/a"
            reason = row["failure_reason"] or ""
            print(
                f"  t={_format_float(row['time'], digits=1)} "
                f"success={row['success']} "
                f"path={path} "
                f"delay={_format_float(row['route_storage_delay'])} "
                f"fidelity={_format_float(row['route_fidelity'])} "
                f"objective={_format_float(row['objective_score'])} "
                f"reason={reason}"
            )
    print()


def main() -> None:
    zero_results = run_many(_cases_for_policy("zero_policy"))
    contact_results = run_many(_cases_for_policy("contact_window_age"))

    print("# QUASAR storage-delay diagnostics demo")
    print()
    print("This is a smoke-test diagnostic demo, not full paper-scale evaluation.")
    print("This is not 24h paper-scale evaluation.")
    print("WalkerDeltaLiteSource is simplified deterministic, not full TLE/SGP4.")
    print("contact_window_age is sampled contact-window-derived delay.")
    print("This is not full entanglement scheduling.")
    print("This is not resource reservation.")
    print("This is not queueing.")
    print()

    _print_summary_table(
        "zero_policy summary",
        results_summary_rows(zero_results),
    )
    _print_summary_table(
        "contact_window_age summary",
        results_summary_rows(contact_results),
    )
    _print_route_diagnostics(
        "zero_policy route diagnostics",
        zero_results,
    )
    _print_route_diagnostics(
        "contact_window_age route diagnostics",
        contact_results,
    )


if __name__ == "__main__":
    main()
