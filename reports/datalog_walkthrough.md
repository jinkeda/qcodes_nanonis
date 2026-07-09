# Datalog Vertical — Implementation Walkthrough

Implemented: 2026-07-02

## Outcome

The datalog vertical now records one or more Nanonis Signals slots on a
deadline schedule and returns an immutable `TimeTraceResult`. Acquisition is
read-only: the workflow sends `Util.VersionGet`, optional `Signals.NamesGet`,
and one `Signals.ValsGet` per sample. It never sends a `Set` command, changes
controller state, writes a Nanonis file, or imports QCoDeS.

The local `TCPProtocol_SPM.pdf` was checked against `Signals.json`.
`Signals.ValsGet` takes an int32 array element count, an int32 index array, and
the uint32 wait flag; it returns an int32 element count followed by float32
values. The existing command transcription matches that contract.

## Public API

```python
from nanonis.workflows import (
    CancelToken,
    NaNPolicy,
    TimeTraceConfig,
    TimeTraceWorkflow,
    cancel_on_sigint,
)

config = TimeTraceConfig(
    signal_indexes=(0, 1),
    duration_s=60.0,
    sample_interval_s=0.1,
    wait_for_newest_data=True,
    resolve_names=True,
)
token = CancelToken()

with cancel_on_sigint(token):
    result = TimeTraceWorkflow(
        nanonis, nan_policy=NaNPolicy.WARN
    ).run(config, cancel=token)
```

For this example, `n_samples` is 601: nominal ticks run from 0 through 60 s,
inclusive. Ratios within `1e-9` of an integer are treated as that integer, so
`0.3 / 0.1` produces four samples instead of losing the final tick to binary
floating-point rounding.

## Cancellation and progress

`workflows/cancellation.py` provides a thread-safe `CancelToken` backed by
`threading.Event`, immutable `ProgressEvent` values, safe callback dispatch,
and `cancel_on_sigint`.

The first SIGINT in the context requests cooperative cancellation. A second
SIGINT raises `KeyboardInterrupt`. The polling loop checks the token at the
start of every iteration and uses `CancelToken.wait()` for interruptible waits.
Consequently a late loop that no longer sleeps remains cancellable. Deliberate
cancellation returns the acquired prefix with `cancelled=True`; transport and
response failures still raise.

Progress is reported approximately once per second and once at termination.
Callback exceptions are logged and suppressed so UI/reporting code cannot
abort acquisition.

## Configuration and result models

`TimeTraceConfig` is frozen and validates:

- non-empty, unique signal slots in `[0, 127]`;
- finite positive duration and interval, with duration at least one interval;
- the float-safe inclusive sample count;
- at most 10,000,000 signal elements.

The cap bounds final value storage at about 80 MB as float64. Peak transient
usage is about 160 MB because the frozen result defensively copies the
preallocated workflow buffer.

`TimeTraceResult` stores actual monotonic offsets, a `(signals, samples)`
float64 matrix, resolved names, UTC start/finish provenance, late-sample count,
cancellation status, and the Nanonis version. Arrays are copied and marked
read-only. Shapes and strictly increasing elapsed time are enforced.

Use `signal_by_index()` for an unambiguous slot lookup. `signal_by_name()`
rejects unresolved, missing, and duplicate names; duplicate-name errors list
the matching indexes. `to_metadata()` echoes signal indexes, requested duration
and interval, the wait mode, and name resolution alongside JSON-compatible
acquisition, controller, package-version, and git-commit provenance without
duplicating the bulk arrays.

The package/git helper now lives in top-level `nanonis.provenance`.
`nanonis.data._utils` delegates to it, preserving the existing data-reader API
without introducing a workflow-to-data dependency.

## Polling and scheduling behavior

The workflow preallocates both output buffers and issues one `ValsGet` for all
requested slots on each tick. It records elapsed time after the response is
received. On platforms whose monotonic clock cannot distinguish two adjacent
reads, the second value is advanced by the smallest representable float64 step
to preserve the result's strict ordering invariant.

Lateness is measured when acquisition starts, after any wait. The fixed
tolerance is half the requested interval, and sample zero is never counted as
late. While jitter remains within tolerance, the next deadline stays on the
nominal grid. Only a counted overrun rebases the next deadline to one interval
after the late acquisition start. This prevents catch-up bursts and skipped
samples while avoiding accumulated sleep-jitter drift.

Every `ValsGet` response must be a mapping containing an integer declared count
and a one-dimensional numeric array. The declared count, actual length, and
requested signal count must all agree. Name resolution similarly requires a
declared name count that matches the array and covers every requested slot.
Malformed responses raise `TimeTraceResponseError` rather than returning a
partial trace.

`Util.VersionGet` runs once before acquisition. Only a controller-reported
`NanonisCommandError` maps to `nanonis_version=None`; timeout, connection, and
protocol failures propagate before any samples are taken.

## Non-finite data

`inspect_non_finite_trace()` reports NaN/Inf counts and affected signal indexes
and names. `NaNPolicy.ALLOW` returns silently, `WARN` logs diagnostics, and
`RAISE` raises `NonFiniteTimeTraceDataError`. The exception retains both the
completed immutable result and its diagnostics.

## Live scripts

`examples/datalog_live_demo.ipynb` is the complete manual tutorial. It covers
every public datalog/cancellation API, guarded connection and signal selection,
short traces, result accessors and plots, offline error/NaN demonstrations,
timer and SIGINT cancellation, state-equality checks, optional 60-second
acceptance, and local NPZ/JSON persistence.

`examples/characterize_signals.py` is the read-only M5a-1 characterization
script. It records the slot table, compares `ValsGet`, `ValGet`, and
`ZCtrl.ZPosGet`, measures latency and inter-arrival distributions for both wait
modes, and estimates the observed Z-slot float32 step.

`examples/live_time_trace.py` is the M5a-4 acceptance script. After rig-specific
Z/current slot indexes are filled in, it records the 60 s/10 Hz trace, computes
the timing gates, performs Z cross-checks outside the timed loop, exercises
graceful Ctrl-C, and compares before/after bias, setpoint, feedback, and RT
snapshots. Both scripts write timestamped JSON reports. They were not executed
as part of offline implementation because no live controller was connected.

## Verification

```text
pytest -q
260 passed

ruff check <changed Python files and tests>
All checks passed!
```

The new 43-test targeted suite covers cancellation, SIGINT restoration,
callback isolation, config/sample-count validation, strict values/names
responses, immutable result accessors, cancellation while late, transport
failure propagation, all NaN policies, overrun rebasing, provenance behavior,
and the zero-write command sequence.

Repository-wide Ruff still reports pre-existing unused imports in
`examples/scan_workflow_live_demo.ipynb`; the datalog files themselves are
clean.
