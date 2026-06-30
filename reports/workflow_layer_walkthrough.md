# Workflow Layer Implementation Walkthrough

Date: 2026-06-30

## Goal of the task

The repository previously exposed low-level TCP commands and thin QCoDeS
parameters, but it did not provide a safe way to run a complete measurement.
Callers had to configure Bias Spectroscopy, start it, interpret its response, and
restore instrument state themselves. A timeout or cleanup exception could leave
the TCP stream out of sync, leave spectroscopy running, overwrite module settings,
or hide valid acquired data.

This task implemented the concrete M0A-M3 work in
`reports/workflow_layer_plan.md`:

- transport and decoder correctness for long-running commands;
- complete Bias Spectroscopy command schemas;
- one recovery-gated restoration transaction;
- explicit, rig-specific safety and bias-restoration policies;
- typed snapshot-and-patch configuration;
- an end-to-end Bias Spectroscopy workflow;
- lossless result normalization and non-finite-data handling; and
- acquire-first QCoDeS persistence.

The intended improvement is a workflow API that can safely execute a bias sweep
as one operation and return a self-describing, immutable result while preserving
the existing dependency direction:

```text
nanonis.workflows -> CommandClient protocol -> NanonisController
nanonis.qcodes.spectroscopy -> nanonis.workflows result models
```

The workflow package does not import QCoDeS, pandas, or pickle. QCoDeS remains an
optional adapter at the outer layer.

## Summary of changes

### New workflow package

The following files were added under `src/nanonis/workflows/`:

- `protocols.py` defines the structural `CommandClient` and
  `RecoverableCommandClient` protocols. `NanonisController` satisfies these
  protocols; no parallel command client was created.
- `errors.py` defines `WorkflowError`, `SafetyPreflightError`,
  `SpectroscopyResponseError`, `RecoveryError`, `StateRestorationError`, and
  `NonFiniteSpectroscopyDataError`.
- `models.py` defines configuration, safety, timing, advanced settings, complete
  Bias Spectroscopy settings, bias-ramp policy, and reconstructed sweep axes.
- `state.py` defines `TipState`, `RecoveryReport`,
  `recover_bias_spectroscopy()`, and `RestorationTransaction`.
- `result.py` defines immutable result, trace, parameter, and non-finite diagnostic
  models plus response normalization.
- `bias_spectroscopy.py` defines `BiasSpectroscopyWorkflow`, hardware preflight,
  bias-range parsing, acquisition-time estimation, and the convenience factory.
- `__init__.py` exposes the supported public workflow API.

### Transport and command-layer changes

- `src/nanonis/protocol/tcp_client.py` now tracks `TransportState`, holds an I/O
  lock across each complete request/response exchange, supports temporary
  per-command timeouts, validates response framing, and invalidates streams after
  transport failures.
- `src/nanonis/protocol/__init__.py` and `src/nanonis/__init__.py` export
  `TransportState`.
- `src/nanonis/command/controller.py` now accepts `timeout=` on `send()` and
  `send_raw()`, exposes `transport_state`, and provides `reconnect()`.
- `src/nanonis/command/encoder.py` now validates the complete response body:
  expected fields, the mandatory error trailer, description length, UTF-8, and
  unexplained trailing bytes.
- `src/nanonis/qcodes/instrument.py` forwards per-command timeouts through its
  direct `send()` method.
- `src/nanonis/command/proxies.py` received an unused-import cleanup only.

### Command schema changes

`configs/commands/BiasSpectr.json` now includes the manual-verified commands that
the workflow requires:

- `BiasSpectr.Stop`;
- `BiasSpectr.StatusGet`;
- `BiasSpectr.AdvPropsSet`;
- `BiasSpectr.LimitsSet`; and
- `BiasSpectr.TimingSet`.

The `TimingSet` order is exactly: Z averaging time, Z offset, initial settling,
maximum slew rate, settling, integration, end settling, and Z control time.
`StatusGet` is a uint32 with `0` meaning stopped and `1` meaning running.

### QCoDeS adapter

`src/nanonis/qcodes/spectroscopy.py` was added with:

- `create_bias_spectroscopy_measurement()`;
- `register_bias_spectroscopy()`;
- `add_bias_spectroscopy_result()`;
- `RegisteredBiasSpectroscopy`; and
- `RegisteredTrace`.

`src/nanonis/qcodes/__init__.py` exports these APIs.

### Tests

The implementation added:

- `tests/test_tcp.py` for transport timeouts, partial reads, invalid headers,
  stream state, and temporary command timeouts;
- `tests/test_schema.py` for Bias Spectroscopy schemas and binary trailer
  alignment; and
- `tests/workflows/` for fake controllers, recovery, restoration, configuration,
  preflight, normalization, the complete workflow, and QCoDeS registration.

Existing controller tests were updated to use the protocol-mandated eight-byte
success trailer. Existing codec tests explicitly exercise body-only decoding.

## Implementation details

### Phase M0A: complete, verified command schemas

The new setters and status/stop commands were derived from the bundled
`TCPProtocol_SPM.pdf`, not inferred from getter field order. Relevant PDF pages
43-48 were text-extracted and visually rendered before the JSON was changed.

`tests/test_schema.py` protects three important wire-level invariants:

1. `PropsGet` produces the expected 12 snake-case runtime fields.
2. A binary `PropsGet` fixture places `autosave` and `show_save_dialog` before the
   error trailer, preventing the previous field-shift failure.
3. `PropsSet`, `TimingSet`, `AdvPropsSet`, `LimitsSet`, `Stop`, and `StatusGet`
   have the expected argument counts and types.

Live-controller validation is still required; see Limitations.

### Phase M0B: long commands and transport correctness

`NanonisTCPClient.send_raw()` now accepts a keyword-only timeout. It acquires a
reentrant `_io_lock`, stores the socket's previous timeout, applies the command
timeout, sends the complete request, receives the complete response, and restores
the previous timeout before releasing the lock. `timeout=None` applies the
controller default; it never means an infinite wait.

The receive path now distinguishes failure categories:

- `socket.timeout` remains a timeout and becomes `NanonisTimeoutError`;
- socket errors and premature EOF become `NanonisConnectionError`; and
- bad command names, non-zero response reserved bytes, malformed command padding,
  negative/oversized body lengths, and invalid UTF-8 become
  `NanonisProtocolError`.

Any of those failures closes the socket and sets
`TransportState.DESYNCHRONIZED`. A successful `reconnect()` creates a new stream
and returns it to `READY`.

Framing and body semantics remain separate. The TCP layer only validates the
40-byte header and declared body. `CommandDecoder` validates command-specific
fields and the final error trailer. A decode error after a full read therefore
does not incorrectly mark the byte stream out of sync.

### Phase M0D/M1: recovery and restoration

`RestorationTransaction` is the single cleanup coordinator. Typed state objects
retain their own restore logic; the transaction only handles ordering, gating,
aggregation, and result retention.

Participants are registered in snapshot order and restored in reverse. The Bias
Spectroscopy workflow registers tip state first and module settings second, so
cleanup runs in this order:

1. Bias Spectroscopy channels;
2. sweep limits;
3. timing;
4. properties;
5. advanced properties;
6. disable Z feedback;
7. restore bias;
8. restore current setpoint; and
9. restore the original feedback state last.

Each participant performs best-effort restoration and returns field-specific
failures. The transaction combines them into one `StateRestorationError`, so a
tip failure cannot mask a module-settings failure.

`recover_bias_spectroscopy()` implements the required recovery sequence:

1. reconnect using a fresh TCP stream;
2. query `BiasSpectr.StatusGet` first;
3. return immediately if already stopped;
4. otherwise send `BiasSpectr.Stop`;
5. poll status with `time.monotonic()` until stopped or the recovery timeout; and
6. return a `RecoveryReport`.

Restoration writes are allowed only when `transport_ready` is true and
`spectroscopy_stopped` is exactly true. A failed reconnect, an unconfirmed stop,
or a second `KeyboardInterrupt` prevents every restoration write. In the
second-interrupt case, `spectroscopy_stopped` is `None`; the resulting
`StateRestorationError` retains the first interrupt as `original_error` and the
second as `recovery_error`.

`TipState` supports three explicit bias-restoration modes:

- `DIRECT` performs one `Bias.Set` after the zero-crossing check;
- `STEPPED` divides the movement into steps no larger than `max_step`, optionally
  dwelling between steps; and
- `EXTERNAL` calls a rig-provided restoration callback.

There is no hidden default safety limit or false FolMe ramp. The user must inject
a `BiasSpectroscopySafetyPolicy` with rig-approved bias, Z-offset, slew-rate,
zero-crossing, feedback, and restoration choices.

### Phase M2: configuration and workflow execution

`BiasSpectroscopyConfig` performs I/O-free validation when constructed. It rejects
invalid point/sweep counts, missing or duplicate channels, negative indexes,
non-finite voltages and overrides, invalid recovery timing, and equal sweep
limits before a command can be sent.

Optional timing and Z-offset fields use `None` to mean “preserve the current
value.” The workflow reads a full `BiasSpectroscopySettings`, applies only the
requested changes with `patch()`, sends complete setter argument lists, and then
snapshots the settings again. This readback is stored as the authoritative
`result.effective_settings`.

One readable Z-offset is used. `TimingGet.z_offset` is the snapshot source, and
the same patched value is sent to both `PropsSet` and `TimingSet`.

Unless `unsafe_skip_preflight=True`, the workflow performs these live checks
before opening or configuring Bias Spectroscopy:

- parse the active text returned by `Bias.RangeGet` into numeric bounds;
- reject an unknown range format;
- enforce both the active range and the policy's absolute bias limit;
- validate every requested channel against the live `Signals.NamesGet` length;
- enforce requested Z-offset and slew limits; and
- reject an already-running spectroscopy module.

After snapshot and patch, the effective readback is checked against the safety
policy again. The readback records any clipping or ignored request as result
provenance, and the workflow stops if the resulting effective value violates a
safety bound.

The acquisition duration estimate includes initial settling, Z control, Z
averaging, all sweeps and directions, the greater of sampling time or slew time,
and end settling. The workflow uses `estimate * 1.5 + 5` seconds unless the user
provides `acquisition_timeout`. A zero or non-finite maximum slew rate cannot
divide by zero; it triggers a warning and a conservative minimum 60-second
estimate. Both the estimate and the actual timeout passed to `Start` are stored
on the result.

`BiasSpectr.Start` is timed with timezone-aware UTC wall-clock timestamps and
`time.monotonic()` duration. Transport errors and `KeyboardInterrupt` trigger the
reconnect/stop recovery before the transaction can restore anything.

### Result normalization

`normalize_bias_spectroscopy_response()` preserves the complete channel-major
matrix. It validates declared dimensions, matrix shape, channel-name count, and
parameter count without assuming that columns equal requested points or that a
measured bias channel exists.

`BiasSpectroscopyResult.__post_init__()` copies the source matrix and marks the
owned copy read-only. `traces()` returns read-only row views, so duplicate channel
names and row order are retained without copying every channel. Duplicate names
receive occurrence-aware convenience names such as `Current (A)#2`.

Fixed parameter names precede varying parameter names, matching the protocol.
When a controller returns more values than known names, the extra
`SpectroscopyParameter.name` values are `None` rather than causing data loss.

`NaNPolicy` is explicit:

- `ALLOW` returns data silently;
- `WARN` is the default and reports NaN/Inf counts and affected channels; and
- `RAISE` raises `NonFiniteSpectroscopyDataError` with the fully built result in
  `exc.result`.

Forward and backward `SweepAxis` values are clearly marked as reconstructed from
configured limits, never as measured bias.

### Phase M3: QCoDeS persistence

Persistence is acquire-first because channel names are unknown until `Start`
returns. `create_bias_spectroscopy_measurement()` creates a `Measurement` from a
finished result and delegates schema creation to `register_bias_spectroscopy()`.

Every trace depends on an array-valued `sample_index`. For a forward-only result
whose column count matches effective points, traces additionally depend on an
independent `configured_voltage` axis. The two axes are independent because
QCoDeS forbids chained dependencies. Backward results do not receive a single
forward voltage axis; `sample_index` remains valid until simulator work identifies
individual trace directions.

Raw labels remain human-readable while QCoDeS identifiers are ASCII-sanitized and
collision-free. For example, two `Current (A)` rows register as `current_a` and
`current_a_2`.

`add_bias_spectroscopy_result()` writes both axes and all trace arrays in one
call, checks that the registered schema still matches the result, and stores:

- acquisition start and finish UTC timestamps;
- monotonic duration;
- estimated duration and timeout used;
- requested config;
- effective readback settings;
- save base name; and
- discovered saved paths.

Passing a `station` to `create_bias_spectroscopy_measurement()` lets QCoDeS attach
its normal station snapshot.

## What has been achieved

The following functionality now works:

- a complete bias sweep can be configured, acquired, normalized, and restored
  through one `BiasSpectroscopyWorkflow.run()` call;
- real sweeps are no longer constrained by the controller's ten-second default
  timeout;
- receive timeouts are correctly classified instead of being swallowed as generic
  connection errors;
- malformed or mismatched response headers are rejected;
- command response trailers cannot be silently truncated or shifted;
- a timed-out/partial response socket is never reused;
- a potentially still-running spectroscopy measurement is stopped and confirmed
  before restoration;
- tip state and module settings restore in a deterministic, best-effort order;
- all cleanup failures and the original failure are simultaneously inspectable;
- valid data survives cleanup failure through `StateRestorationError.result`;
- configuration no longer overwrites existing timing with unsafe zero defaults;
- returned data remains ordered and lossless even with duplicate channel names;
- NaN/Inf handling is explicit and can retain partial acquisitions; and
- completed results can be inserted into a real QCoDeS dataset with correct axes
  and acquisition-time metadata.

## How to use it

The numeric safety values below are examples only. They must be replaced with
limits approved for the actual rig.

```python
from nanonis.command import NanonisController
from nanonis.workflows import (
    BiasRestoreMode,
    BiasSpectroscopyConfig,
    BiasSpectroscopySafetyPolicy,
    BiasSpectroscopyWorkflow,
    NaNPolicy,
)

policy = BiasSpectroscopySafetyPolicy(
    max_abs_bias=2.0,          # V; replace with a rig-approved limit
    max_abs_z_offset=100e-9,   # m
    min_slew_rate=1e-3,        # V/s
    max_slew_rate=10.0,        # V/s
    bias_restore_mode=BiasRestoreMode.DIRECT,
    bias_ramp=None,
    allow_zero_crossing=False,
)

config = BiasSpectroscopyConfig(
    start_voltage=-0.2,
    stop_voltage=0.2,
    points=401,
    channel_indexes=(0, 24),
    sweeps=2,
    include_backward=False,
    integration_time=0.01,
    settling_time=0.005,
    maximum_slew_rate=1.0,
    save_base_name="sts/example",
)

with NanonisController(
    "127.0.0.1", 6501, "configs/commands"
) as controller:
    workflow = BiasSpectroscopyWorkflow(
        controller,
        safety_policy=policy,
        nan_policy=NaNPolicy.WARN,
    )
    result = workflow.run(config)

print(result.channel_names)
print(result.data.shape)               # rows are channels, columns are samples
print(result.effective_settings)       # authoritative controller readback
print(result.acquisition_timeout_used)
```

For stepped restoration, provide a `BiasRampPolicy` and select `STEPPED`:

```python
from nanonis.workflows import BiasRampPolicy, ZeroCrossingPolicy

ramp = BiasRampPolicy(
    max_step=0.01,
    dwell_time=0.05,
    zero_crossing_policy=ZeroCrossingPolicy.FORBID,
)
policy = BiasSpectroscopySafetyPolicy(
    max_abs_bias=2.0,
    max_abs_z_offset=100e-9,
    min_slew_rate=1e-3,
    max_slew_rate=10.0,
    bias_restore_mode=BiasRestoreMode.STEPPED,
    bias_ramp=ramp,
    allow_zero_crossing=False,
)
```

If acquisition succeeds but restoration fails, salvage the attached result before
re-raising or alerting the operator:

```python
from nanonis.workflows import StateRestorationError

try:
    result = workflow.run(config)
except StateRestorationError as exc:
    if exc.result is not None:
        persist_result(exc.result)
    if isinstance(exc.original_error, KeyboardInterrupt):
        handle_operator_interrupt()
    raise
```

Persist a completed result with QCoDeS as follows:

```python
from nanonis.qcodes import (
    add_bias_spectroscopy_result,
    create_bias_spectroscopy_measurement,
)

measurement, registered = create_bias_spectroscopy_measurement(
    experiment,
    result,
    station=station,
)
with measurement.run() as datasaver:
    add_bias_spectroscopy_result(datasaver, registered, result)
```

`unsafe_skip_preflight=True` exists for controlled simulator/testing scenarios.
It should not be used as the normal hardware path. Structural validation and
hard policy checks still apply.

## Validation and testing

### Automated tests

The final plain test run completed successfully:

```text
105 passed in 2.08s
```

The tests cover:

- header and mid-body timeouts;
- connection closure during a body;
- bad command names, body sizes, reserved bytes, and transport-state changes;
- temporary per-command timeout restoration;
- schema field counts and a binary `PropsGet` trailer fixture;
- strict decoder trailer validation;
- config and safety-policy validation before I/O;
- stop-and-wait recovery and already-stopped fast paths;
- failed reconnect and unconfirmed-stop write gating;
- a second interrupt during recovery;
- reverse participant order and aggregated failures;
- direct and stepped tip restoration;
- snapshot, patch, readback, and restoration command order;
- the shared PropsSet/TimingSet Z-offset;
- computed and explicit acquisition timeouts;
- response dimensions, duplicate names, frozen data, and trace views;
- NaN/Inf diagnostics with retained result;
- timestamp validation and reconstructed axes; and
- QCoDeS axis selection, identifier sanitization, insertion, and metadata.

### Static and structural checks

These checks passed:

```text
ruff check src tests
python -m compileall -q src
git diff --check
BiasSpectr.json parsed with ConvertFrom-Json
```

Mypy reports no errors in the new workflow implementation itself. A repository
run still reports nine existing errors in the older command proxy and QCoDeS
channel modules (three `Any` returns and QCoDeS `InstrumentModule` stub/signature
issues). Those modules were not refactored as part of this task.

A coverage-instrumented pytest run could not collect tests in this Windows/Python
environment because NumPy raised `ImportError: cannot load module more than once
per process` under the coverage plugin. Plain pytest consistently passes, so no
coverage percentage is claimed.

### Real QCoDeS database validation

In addition to mock-based tests, the adapter was run against installed QCoDeS
0.54.4 using a temporary SQLite database. The validation created run ID 1 with:

```text
sample_index, configured_voltage, current_a, current_a_2
```

It inserted the array data and all nine workflow metadata fields. This test found
and corrected a chained-dependency design that QCoDeS rejects: voltage and sample
index are now independent axes of each trace.

## Remaining limitations and known issues

### M0C simulator and live-controller validation

No live Nanonis controller or controller simulator was reachable in this task.
The following plan items therefore remain intentionally unclaimed:

- raw live validation of corrected `PropsGet` trailer alignment;
- confirmation that writing Z-offset through `PropsSet` and `TimingSet` changes
  the same underlying setting;
- exact result shape/name behavior for backward sweeps, multiple sweeps, and
  “save all”;
- identification of individual backward traces for per-trace voltage axes;
- confirmation of parameter name/value ordering across controller versions;
- autosaved-file behavior and `saved_paths`; and
- confirmation of the proposed module-restoration order on the simulator.

The implementation preserves raw rows/columns and avoids encoding assumptions for
these unresolved cases.

### Bias safety remains a lab decision

The software makes restoration policy explicit, but it cannot decide whether a
specific rig may cross zero, whether feedback must be off, or which direct/step
limits are safe. Those values and choices must be reviewed by the lab. A direct
mode is not automatically safe merely because it is available.

### M4 second workflow

The plan names M4 only as “prefer scan or data-logging” and does not define a
state model, safety policy, timeout/recovery contract, result model, or simulator
acceptance criteria. The repository has enough scan commands to implement a real
scan workflow, but starting one without those decisions would repeat the unsafe
assumptions this task removed. M4 is therefore the next vertical, not part of the
completed Bias Spectroscopy contract.

## Next steps

1. Run the M0C characterization matrix on a Nanonis simulator: forward, backward,
   averaged, averaged plus backward, and save-all on/off. Record channel names,
   matrix shapes, parameter arrays, and file behavior.
2. Run `scripts/live_test_commands.py` against a controller after adding the five
   new Bias Spectroscopy commands to the live-test selection.
3. Approve and version a real `BiasSpectroscopySafetyPolicy` for each rig,
   including zero-crossing and interrupted-ramp procedures.
4. Decide backward-row identification from simulator evidence, then add per-trace
   forward/backward QCoDeS voltage axes.
5. Populate `saved_paths` only after controller/autosave file behavior is known.
6. Specify M4 before coding it. A scan workflow should define scan configuration
   snapshot/restore, stop-and-wait recovery, frame result ownership, and safety
   preflight with the same rigor as Bias Spectroscopy.
7. Optionally clean up the nine legacy Mypy errors and investigate the
   pytest-cov/NumPy loader conflict so coverage can be measured reliably.
