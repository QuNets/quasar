"""Paper-aligned QUASAR experiment smoke demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quasar.experiments import ExperimentConfig, QuasarExperimentRunner  # noqa: E402


def _format_float(value, digits=4, suffix=""):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}"


def _print_config(config):
    baseline = config.baseline
    print("Baseline configuration")
    print("ground-station pair: Houston -> Washington-DC")
    print("scenario source:     WalkerDeltaLiteSource")
    print(f"architecture:        {config.architecture.upper()}")
    print(f"routing workload:    {config.routing_algorithm.upper()}")
    print(f"time points:         {config.time_points}")
    print(f"planes:              {config.planes}")
    print(f"satellites/plane:    {config.satellites_per_plane}")
    print(f"altitude:            {_format_float(baseline.altitude_km, digits=1, suffix=' km')}")
    print(f"inclination:         {_format_float(baseline.inclination_deg, digits=1, suffix=' deg')}")
    print(f"dt:                  {_format_float(baseline.dt, digits=1, suffix=' s')}")
    print(f"min elevation:       {_format_float(baseline.min_elevation_deg, digits=1, suffix=' deg')}")
    print(f"eta0:                {baseline.eta0:.1e}")
    print(f"alpha:               {_format_float(baseline.alpha)}")
    print(f"h0:                  {_format_float(baseline.h0_km, digits=1, suffix=' km')}")
    print(f"kappa:               {_format_float(baseline.kappa)}")
    print(f"zeta_swap:           {_format_float(baseline.zeta_swap)}")
    print(f"F0:                  {_format_float(baseline.f0)}")
    print(f"fidelity threshold:  {_format_float(baseline.fidelity_threshold)}")
    print(f"tau_c:               {_format_float(baseline.tau_c, digits=1, suffix=' s')}")
    print()


def _print_result(result):
    summary = result.summary.to_dict()
    metadata = result.metadata
    route_attempts = len(result.route_results)
    route_successes = sum(1 for route in result.route_results if route.success)
    print("Experiment result")
    print(f"snapshots:              {len(result.snapshots)}")
    print(f"route attempts:         {route_attempts}")
    print(f"route successes:        {route_successes}")
    print(f"routing success rate:   {_format_float(summary['routing_success_rate'])}")
    print(f"total candidate edges:  {metadata['total_candidate_edges']}")
    print(f"total available edges:  {metadata['total_available_edges']}")
    print(
        "topology edge ratio:    "
        f"{_format_float(metadata['topology_available_edge_ratio'])}"
    )
    print(f"total events:           {summary['total_events']}")
    print(f"trace edge ratio:       {_format_float(summary['available_edge_ratio'])}")
    print(f"average transmittance:  {_format_float(summary['average_transmittance'])}")
    print(f"average fidelity:       {_format_float(summary['average_fidelity'])}")
    print("event counts:")
    for event_type, count in sorted(summary["event_counts"].items()):
        print(f"  {event_type}: {count}")
    print()


def main() -> None:
    config = ExperimentConfig(
        planes=6,
        satellites_per_plane=10,
        time_points=(0.0, 300.0, 600.0, 900.0, 1200.0, 1500.0),
    )
    result = QuasarExperimentRunner(config).execute()

    print("# QUASAR experiment demo")
    print()
    print("This is a smoke-test experiment, not 24h paper-scale evaluation.")
    print("WalkerDeltaLiteSource is simplified deterministic, not full TLE/SGP4.")
    print("storage_delay is zero_policy, not contact-schedule-derived.")
    print()
    _print_config(config)
    _print_result(result)


if __name__ == "__main__":
    main()
