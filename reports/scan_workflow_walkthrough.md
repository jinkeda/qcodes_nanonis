# Scan Workflow Layer — Implementation Walkthrough

Date: 2026-06-30

## Goal of the task

Implement the M4 scan vertical described in
[`scan_workflow_plan.md`](scan_workflow_plan.md) without coupling measurement
orchestration to QCoDeS. The finished workflow must:

- validate a one-frame scan against explicit rig safety limits;
- snapshot, patch, apply, read back, and restore scan settings;
- force continuous scanning off for a finite acquisition;
- start in the PDF-defined direction, wait with separate controller and socket
  timeouts, and grab every requested channel/direction image;
- stop and confirm the scan module after any unconfirmed post-start failure;
- return an immutable, self-describing `ScanResult`; and
- preserve the existing bias-spectroscopy behavior while generalizing the shared
  recovery and tip-restoration toolkit.

The scan workflow depends only on `CommandClient`. QCoDeS persistence remains a
deliberately deferred adapter boundary.

## Summary of changes

### New scan workflow package

`src/nanonis/workflows/scan/` now contains:

- `models.py`: `ScanConfig`, `ScanSafetyPolicy`, `ScanFrame`, `ScanSpeed`,
  `ScanProps`, and `ScanSettings`, including asymmetric Get/Set enum conversions;
- `result.py`: immutable `ScanChannelImage` and `ScanResult` models, response
  normalization, and scan-specific non-finite-data handling;
- `workflow.py`: preflight, duration and timeout calculation, recovery,
  frame grabbing, `ScanWorkflow`, and the `scan(...)` factory; and
- `__init__.py`: the public scan API.

The public symbols are also exported from `nanonis.workflows`.

### Shared toolkit generalizations

`RecoveryReport` now uses the vertical-neutral `module_stopped` field. Its
read-only `spectroscopy_stopped` property keeps the prior API working.
`recover_module(...)` owns reconnect → status query → stop → bounded poll, while
`recover_bias_spectroscopy(...)` and `recover_scan(...)` provide thin command
bindings. Recovery error text no longer names BiasSpectr, and
`RestorationTransaction.record_recovery()` accepts an omitted origin.

`TipRestorePolicy` now contains the shared bias/setpoint/feedback restoration
choices. `BiasSpectroscopySafetyPolicy` retains its original constructor and
exposes the shared portion through `.tip`; the spectroscopy regression suite is
unchanged at call sites except for passing that composed policy to `TipState`.

### Command schemas and direction encoding

The command registry now includes the PDF-verified schemas for:

- `Scan.FrameSet`: five `float32` arguments, with no wait flag;
- `Scan.SpeedSet` and `Scan.SpeedGet`: four `float32` values, one `uint16`
  selector, and a `float32` ratio; and
- `Piezo.RangeGet`: X, Y, and Z `float32` ranges.

`Scan.BufferGet` pixels and lines are corrected to signed `int32` fields.
`Scan.WaitEndOfScan` now exposes the normalized `timeout_status` key.

The existing command proxy and QCoDeS channel direction bug is corrected:
`up=1`, `down=0`. The workflow uses named constants rather than deriving those
wire values independently.

### Deferred QCoDeS seam

`nanonis.qcodes.scan` exposes `register_scan_result(...)` and
`add_scan_result(...)`. Both intentionally raise `NotImplementedError` with a
message pointing back to the plan. This makes the future persistence boundary
explicit without inventing a physical row orientation that has not been checked
on hardware.

## Implementation details

### Snapshot, patch, and readback

`ScanSettings.snapshot()` reads `FrameGet`, `BufferGet`, `PropsGet`, and
`SpeedGet`. It retains all readable property state, including bouncy mode,
autopaste, module names, per-module parameter counts, and the parameter-header
table.

`ScanSettings.patch()` changes only non-`None` config fields. A line-time override
selects “time per line” as the controller's constant speed parameter. Continuous
scan is always patched to off because `WaitEndOfScan` cannot complete for a
continuous raster.

Settings are written in a deterministic order:

1. frame;
2. buffer;
3. speed; and
4. properties.

Every setter receives a complete argument list. Read-side enum values are never
echoed into write-side fields: on/off, autosave/autopaste, and speed-selector
values all pass through explicit conversion functions. Restoration uses the same
complete write path in best-effort mode and aggregates failures through the
shared transaction.

### Safety preflight

`ScanSafetyPolicy` makes the rig-dependent limits explicit:

- maximum pixels and lines;
- piezo safety margin;
- minimum and maximum line times; and
- minimum and maximum linear speeds.

Preflight reads the controller's X/Y piezo travel and treats it as total range
about zero. Every clockwise-rotated frame corner must fit inside half-range minus
the safety margin. It also checks signal indexes, effective buffer dimensions,
effective forward/backward timing and speed, and `Scan.StatusGet == idle`.
Unknown, zero, or malformed ranges fail closed.

Structural and directly requested policy checks run before any command is sent.
`unsafe_skip_preflight=True` skips live range/channel/status checks for controlled
tests, but typed configuration validation and effective settings policy checks
remain active.

### Acquisition and timeout model

The workflow measures a complete raster as:

```text
lines × (forward time per line + backward time per line) + 1 s positioning margin
```

Saved data directions do not multiply this estimate: the scanner performs both
line movements regardless of which buffers are later grabbed. Invalid or zero
line timing selects a conservative 60-second estimate instead of dividing by or
scaling with an unusable value.

The Nanonis timeout is the estimate plus a 5000 ms margin. The default socket
timeout is 1.5 times the larger of the estimate and controller timeout, plus five
seconds. An explicit socket timeout must exceed the controller-side timeout.
Both the estimate and resolved socket timeout are retained in the result.

`Scan.Action` starts with `ACTION_START=0` and `DIRECTION_UP=1` or
`DIRECTION_DOWN=0`. A `WaitEndOfScan` status of one raises `ScanTimeoutError`.
Status zero marks completion, after which `FrameDataGrab` is called once for each
channel × requested data direction (`forward=1`, `backward=0`).

Declared response shape must match the returned matrix. A difference between the
grabbed dimensions and effective buffer dimensions is warned about and preserved,
because live-controller orientation and clipping behavior are not yet known.

### Failure recovery and restoration

The workflow tracks `start_attempted` and `completed` independently. Any
`BaseException` after a start attempt and before confirmed completion—including a
Nanonis command error, protocol/transport error, timeout, or
`KeyboardInterrupt`—runs `recover_scan(...)`.

Recovery reconnects, checks `Scan.StatusGet`, sends `Scan.Action(Stop, 0)` when
needed, and polls to a monotonic deadline. Restoration writes are permitted only
when transport is ready and module stop is confirmed. If either condition is
unknown, `StateRestorationError` prevents potentially unsafe writes.

A failure while grabbing data occurs after confirmed completion, so no redundant
stop is issued. The transaction still observes the transport state and blocks
restoration if the socket became desynchronized.

### Result normalization

Each `ScanChannelImage` owns a copied `float64` two-dimensional array and marks it
read-only. It retains:

- controller channel name;
- numeric channel index;
- explicit saved-data direction; and
- explicit scan direction returned by the controller.

`ScanResult` retains the requested config, authoritative effective settings,
frame, saved file path, timezone-aware UTC timestamps, monotonic duration,
duration estimate, and timeout used. Duplicate channel/direction pairs are
rejected.

The existing `NaNPolicy` is reused. `ALLOW` preserves non-finite values silently,
`WARN` reports affected images, and `RAISE` raises `NonFiniteScanDataError` while
keeping the completed result available through `exc.result`.

## What has been achieved

- A scan can be configured, safety-checked, acquired, normalized, and restored
  through one `ScanWorkflow.run()` call.
- Continuous mode cannot accidentally turn a finite workflow into an endless
  wait, and its original state is restored afterward.
- Asymmetric protocol enums are correctly translated in both acquisition and
  restoration paths.
- The PDF-defined scan direction is used consistently by the workflow, command
  proxy, and QCoDeS channel.
- Controller-side and socket-side timeouts are distinct and ordered safely.
- All unconfirmed post-start failures use stop-and-confirm recovery before state
  restoration.
- Valid acquired images survive restoration failure through
  `StateRestorationError.result`.
- Forward and backward images remain distinct, lossless, owned, and immutable.
- The shared recovery and tip policy abstractions now support a second vertical
  without breaking spectroscopy.

## How to use it

The numeric bounds below are examples only. Replace them with values approved for
the actual scanner and tip.

```python
from nanonis.command import NanonisController
from nanonis.workflows import (
    ScanConfig,
    ScanSafetyPolicy,
    ScanWorkflow,
)

policy = ScanSafetyPolicy(
    max_pixels=1024,
    max_lines=1024,
    piezo_safety_margin=20e-9,
    min_line_time=1e-3,
    max_line_time=10.0,
    min_linear_speed=1e-12,
    max_linear_speed=1e-3,
)

config = ScanConfig(
    channel_indexes=(0, 24),
    direction="up",
    center_x=0.0,
    center_y=0.0,
    width=100e-9,
    height=100e-9,
    pixels=256,
    lines=256,
    forward_line_time=0.25,
    backward_line_time=0.10,
    autosave="next",
    series_name="topography",
    data_directions=("forward", "backward"),
)

with NanonisController("127.0.0.1", 6501, "configs/commands") as controller:
    result = ScanWorkflow(controller, safety_policy=policy).run(config)

print(result.saved_path)
for image in result.images:
    print(image.name, image.direction, image.scan_direction, image.data.shape)
```

To restore tunnel conditions as an additional transaction participant, provide a
shared tip policy and opt in through the config:

```python
from nanonis.workflows import BiasRestoreMode, TipRestorePolicy

tip_policy = TipRestorePolicy(
    bias_restore_mode=BiasRestoreMode.DIRECT,
    bias_ramp=None,
    allow_zero_crossing=False,
)
policy = ScanSafetyPolicy(
    max_pixels=1024,
    max_lines=1024,
    piezo_safety_margin=20e-9,
    min_line_time=1e-3,
    max_line_time=10.0,
    min_linear_speed=1e-12,
    max_linear_speed=1e-3,
    tip=tip_policy,
)
config = ScanConfig(channel_indexes=(0,), restore_tip_state=True)
```

If acquisition succeeds but restoration fails, salvage the attached result:

```python
from nanonis.workflows import StateRestorationError

try:
    result = workflow.run(config)
except StateRestorationError as exc:
    if exc.result is not None:
        persist_elsewhere(exc.result)
    raise
```

The QCoDeS scan functions currently raise `NotImplementedError` by design.

## Validation and testing

### Automated tests

The complete test suite passes:

```text
139 passed in 1.33s
```

The new tests cover:

- scan command schema field counts and signed buffer dimensions;
- generic module recovery and the compatibility report alias;
- shared tip policy composition;
- every asymmetric properties/speed enum conversion;
- config validation before I/O;
- pre-write rejection of undersized explicit socket timeouts;
- setter diagnostics that retain the controller exception text;
- malformed scan-status response classification;
- snapshot/patch/apply/readback order and continuous-mode restoration;
- up/down wire constants;
- Nanonis timeout and arbitrary post-start error recovery;
- separate timeout values and forward-plus-backward duration estimation;
- every channel × saved-direction frame grab;
- rotated-frame piezo bounds;
- immutable owned image arrays and explicit directions;
- non-finite result salvage;
- restoration failure result salvage; and
- the intentionally deferred QCoDeS seam.

### Static and structural checks

These checks passed:

```text
ruff check src tests
python -m compileall -q src tests
git diff --check
Scan.json and Piezo.json parsed with ConvertFrom-Json
mypy src/nanonis/workflows src/nanonis/qcodes/scan.py
```

Mypy reports no issues in the workflow packages or scan QCoDeS stub.

## Remaining limitations and known issues

### Live-controller characterization is still required

No Nanonis controller was available during this implementation. The following
cannot honestly be claimed from fake-controller tests:

- whether `FrameDataGrab` rows run bottom-to-top or top-to-bottom;
- whether an up versus down scan reverses row order;
- the real `PropsGet` autopaste encoding on the installed controller version;
- live alignment of every Frame/Buffer/Props/Speed response field; and
- the complete start/wait/grab/restore path over a real socket.

The result therefore preserves raw matrix order and explicit controller scan
direction without flipping or rotating data.

### Safety limits remain rig decisions

The software checks the supplied limits but cannot choose them. Piezo safety
margin, dimension caps, acceptable line timing/speed, zero-crossing behavior, and
tip restoration policy must be reviewed for each scanner.

### QCoDeS persistence is deferred

The plan intentionally postpones the adapter. A future implementation must use
two-dimensional setpoint meshgrids of the same shape as each image. Physical
coordinate grids must wait for the live row-orientation result; scan angle itself
is not the blocker.

## Next steps

1. Run the read-only M4-A characterization against a real controller and record
   raw Frame/Buffer/Props/Speed responses plus forward/backward grab orientation.
2. Run a conservative one-frame acquisition on hardware and verify start, wait,
   saved path, recovery, and restoration event order.
3. Approve and version `ScanSafetyPolicy` values for each rig.
4. Add physical coordinate grids only after row orientation is known.
5. Implement the deferred QCoDeS meshgrid adapter when scan persistence becomes a
   project priority.
