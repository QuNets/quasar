# QUASAR

QUASAR (Quantum Satellite Architecture and Routing Simulator) is a
satellite-based quantum entanglement distribution simulator framework. It
provides modular components for constructing time-varying satellite quantum
network topologies, annotating links with physical channel and memory
attributes, evaluating architecture-specific feasibility, running routing
baselines, and collecting experiment traces.

This public release contains the core framework, tests, and runnable demos used
to exercise the simulator stack, including a small SGP4-backed TLE fixture demo.
Paper-scale 24-hour Walker-Delta sweeps, the 60-satellite Starlink TLE subset,
generated datasets, and final figure-generation scripts are maintained
separately during submission preparation and are not included in this public
repository.

## What Is Included

- Core QUASAR Python package under `quasar/`
- Minimal scenario/data-source layer, including Walker-Delta-lite demos and
  an SGP4-backed TLE fixture demo
- Small public TLE fixture under `examples/data/` for validating trace-driven
  orbital input
- Spatiotemporal topology generation from explicit time-indexed candidate links
- Channel loss, success probability, and memory decoherence helpers
- SD and OOS architecture abstractions
- OOS routing baselines: DSP, MPR, and EASR
- Sampled contact-window timing and storage-delay diagnostics
- Event records, threshold-crossing event bridge, and SimQN-compatible adapter
- Metrics, traces, logs, and experiment summary utilities
- Runnable examples under `examples/`
- Tests under `test/quasar/`

## Core Modules

- `quasar/scenarios/`: interchangeable scenario sources, including
  Walker-Delta-lite, trace replay, and SGP4-backed TLE inputs.
- `quasar/topology/`: sampled dynamic graph construction, visibility masks,
  range constraints, and available edge extraction.
- `quasar/channel/`: optical-channel loss and path success probability helpers.
- `quasar/memory/`: storage-time decoherence and fidelity threshold helpers.
- `quasar/architecture/`: SD and OOS hardware abstraction semantics.
- `quasar/routing/`: SD opportunity selection and OOS DSP/MPR/EASR routing.
- `quasar/timing/`: sampled contact windows and storage-delay estimators.
- `quasar/events/`: QUASAR-native event records, threshold detection, and a thin
  SimQN event adapter.
- `quasar/metrics/`: event logs, edge traces, path traces, metric samples, and
  summaries.
- `quasar/experiments/`: paper-aligned smoke-test configs, runner, batch cases,
  and diagnostics.

## Installation / Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install flake8 pytest
```

The examples are designed to run directly from the repository root.

## Run Tests

```powershell
python -m flake8 quasar test/quasar examples
python -m pytest test/quasar
```

## Run Demos

```powershell
python examples/quasar_scenario_demo.py
python examples/quasar_experiment_demo.py
python examples/quasar_routing_batch_demo.py
python examples/quasar_contact_delay_batch_demo.py
python examples/quasar_storage_delay_diagnostics_demo.py
python examples/quasar_tle_trace_demo.py
```

## Scope Notes

The public release includes Walker-Delta scenario demos and sampled
contact-window storage-delay diagnostics. These are intended for framework
validation, smoke tests, and reproducible demonstrations of the public API.

Paper-scale 24-hour Walker-Delta sweeps, generated datasets, and
figure-generation scripts for final manuscript plots are maintained separately
during submission preparation.

QUASAR exposes timing, channel, and memory attributes for routing and
orchestration algorithms. The public release does not implement full
multi-request entanglement scheduling, memory-slot reservation, or queueing.

The public release includes a small SGP4-backed TLE fixture demo to validate the
trace-driven scenario-source interface. This demo is intended to exercise the
public topology pipeline, not to reproduce the paper-scale Starlink trace
experiment.

Paper-scale 24-hour Walker-Delta sweeps, the 60-satellite Starlink TLE subset,
generated datasets, and final figure-generation scripts are maintained
separately during submission preparation.
