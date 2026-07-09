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

- `models.py`: `ScanConfig`, `ScanSafetyPolicy`, `ScanRegion`, `ScanSpeed`,
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
`Scan.WaitEndOfLine` had a duplicated response field name (`Timeout status
status`) that decoded to `timeout_status_status`; it is corrected to
`timeout_status`, matching `WaitEndOfScan`, so the per-line wait is usable by
`run_partial` (see the 2026-07-01 addendum).

The existing command proxy and QCoDeS channel direction bug is corrected:
`up=1`, `down=0`. The workflow uses named constants rather than deriving those
wire values independently.

### QCoDeS seam (implemented 2026-07-01)

`nanonis.qcodes.scan` exposes `register_scan_result(...)`, `add_scan_result(...)`,
and `create_scan_measurement(...)`. Originally `NotImplementedError` stubs (pending
the row-orientation result), they are now a real acquire-first adapter — see the
2026-07-01 orientation addendum below, which unblocked them. The adapter registers
2-D integer index meshgrids (`row_index`/`col_index`) as setpoints, then each
channel×direction image and optional physical `x_m`/`y_m` grids (from the confirmed
`row_order` via `scan_coordinate_grids`) as dependents, plus provenance metadata.

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

`ScanWorkflow.run_partial(...)` is a second acquisition entry point that stops
after a requested number of image rows using `Scan.WaitEndOfLine` instead of
`WaitEndOfScan`. It reuses the same preflight/snapshot/apply/restore/recovery
scaffolding and is documented in the 2026-07-01 addendum.

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

config = ScanConfig(          # the stable recipe: how to measure
    channel_indexes=(0, 24),
    direction="up",
    pixels=256,
    lines=256,
    forward_line_time=0.25,
    backward_line_time=0.10,
    autosave="next",
    series_name="topography",
    data_directions=("forward", "backward"),
)
region = ScanRegion(          # the per-shot frame: where/what to measure
    center_x=0.0, center_y=0.0, width=100e-9, height=100e-9,
)

with NanonisController("127.0.0.1", 6501, "configs/commands") as controller:
    result = ScanWorkflow(controller, safety_policy=policy).run(config, region)

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
    result = workflow.run(config, region)
except StateRestorationError as exc:
    if exc.result is not None:
        persist_elsewhere(exc.result)
    raise
```

To acquire only the first few image rows — for a quick preview, a drift check, or
to abort a bad frame early — use `run_partial` (see the 2026-07-01 addendum):

```python
returns = []

def on_line(line_number, movement, pass_number):
    returns.append((line_number, movement, pass_number))
    return False if line_number >= 8 else None  # optional early abort

# max_lines counts image rows; partial scans are not auto-saved.
result = ScanWorkflow(controller, safety_policy=policy).run_partial(
    config, max_lines=8, on_line=on_line
)
# Unscanned rows are NaN; read the partial image from the returned result.
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

No Nanonis controller was available during the original implementation. The
2026-07-01 addendum exercised a real controller for the partial-scan work, which
confirmed the `Scan.WaitEndOfLine` semantics and ran the full
start/wait/grab/restore path over a real socket end to end. The following are
still not established and cannot be claimed from fake-controller tests:

- whether `FrameDataGrab` rows run bottom-to-top or top-to-bottom;
- whether an up versus down scan reverses row order;
- the real `PropsGet` autopaste encoding on the installed controller version; and
- live alignment of every Frame/Buffer/Props/Speed response field.

The result therefore preserves raw matrix order and explicit controller scan
direction without flipping or rotating data.

### Safety limits remain rig decisions

The software checks the supplied limits but cannot choose them. Piezo safety
margin, dimension caps, acceptable line timing/speed, zero-crossing behavior, and
tip restoration policy must be reviewed for each scanner.

Piezo limits in particular are treated as a careful, deliberate decision: the
measured travel is 3 um in X/Y and 1.5 um in Z, and any frame that approaches
those edges risks the scanner. For that reason `examples/rig_safety_policies.py`
ships only a **draft** policy, gated behind `require_approved(...)`, which raises
until a qualified operator has reviewed every value, set `approved=True` with an
approval date, and bumped the version. No scan should run against unapproved
piezo limits.

### QCoDeS persistence (implemented; fast axis still assumed)

The adapter (`qcodes/scan.py`) is built. It uses two-dimensional setpoint meshgrids
of the same shape as each image (QCoDeS 0.54 rejects 1-D axes). Physical `x_m`/`y_m`
grids use the confirmed `row_order = "top_to_bottom"`; the fast-axis `column_order`
is not yet characterized, so it defaults to `left_to_right` and a warning is logged
when physical grids are emitted (X may be mirrored until verified). Callers wanting
only the unambiguous index grids can pass `physical_coordinates=False`.

## Addendum (2026-07-01): partial scans and live `WaitEndOfLine` characterization

### New `ScanWorkflow.run_partial(...)`

`run_partial(config, *, max_lines, on_line=None, unsafe_skip_preflight=False)`
acquires at most `max_lines` **image rows** of the frame, then issues
`Scan.Action(Stop)`. It is a sibling of `run`, not a flag on it: the full-frame
path still blocks on a single `WaitEndOfScan`, which is structurally required for
its saved-path/grab/restore contract. The partial path instead drives the raster
line by line:

1. identical read-only preflight, tip snapshot, settings snapshot/patch/apply,
   authoritative readback, and effective-safety check;
2. `Scan.Action(Start, direction)`;
3. a loop over `Scan.WaitEndOfLine(line_timeout_ms)` with a per-line socket
   timeout derived from `nanonis_line_timeout_ms(effective)`;
4. `Scan.Action(Stop, 0)` once the requested rows are counted (or `on_line`
   vetoes, or the frame finishes on its own); and
5. the same `FrameDataGrab` → `normalize_scan` → restore steps as `run`.

Key contracts:

- **`max_lines` counts image rows, not raw returns.** Rows are counted at each
  *trace* return (`movement == TRACE_MOVEMENT == 0`, `line_number >= 1`), which is
  immune to the variable-length startup transient (see characterization below).
- `on_line(line_number, movement, pass_number)` fires after **every**
  `WaitEndOfLine` return (per movement); returning `False` stops the scan
  immediately — the preview/drift-check/early-abort hook.
- Partial scans are not auto-saved, so `result.saved_path` is `""`; unscanned
  rows come back as NaN and are handled by `NaNPolicy` (use `WARN`/`ALLOW`).
- A safety bound (`2 × rows + 6` returns) prevents an unbounded loop if a
  controller's movement encoding differs from the characterized convention; the
  loop then logs a warning and stops cleanly.
- `config.acquisition_timeout` governs the whole-frame `WaitEndOfScan` and is
  ignored here; per-line timeouts are derived internally.

`nanonis_line_timeout_ms` is exported alongside the other acquisition helpers.

### Live `WaitEndOfLine` characterization

A real controller was available for this follow-up. `examples/verify_waitendofline.py`
runs a small partial scan, records every `WaitEndOfLine` return through `on_line`,
and prints a verdict; its pure analysis (`summarize_line_records`) is unit-tested
offline. Two runs on this rig established:

- the tip emits roughly **two returns per image row** — a trace
  (`movement == 0`) then a retrace (`movement == 1`) — with **1-based**
  `line_number`;
- there is a short **startup transient** of variable length (one run showed a
  single `line_number == -1, movement == 3` sentinel; another showed two leading
  returns), so a fixed-length prefix cannot be skipped — counting trace returns
  is the robust rule;
- `Scan.StatusGet` reports running (1) throughout and idle (0) after the stop.

The fix was verified end to end: `run_partial(max_lines=4)` on a 16-line frame
returned exactly four finite data rows (the remaining twelve NaN), and the module
returned to idle. The earlier, raw-return-counting implementation produced only
two rows for the same request — the defect this characterization caught and fixed.

Row orientation (top-to-bottom vs bottom-to-top, and whether up/down flips it)
remains uncharacterized; `run_partial` preserves raw matrix order exactly like
`run`.

### Tests after the addendum

```text
152 passed
```

Added or revised coverage: row counting by trace returns, `max_lines` capped at
the frame line count, `on_line` early abort, early stop when status reads idle,
the no-rows-counted warning path, per-line timeout recovery, positive-`max_lines`
validation, and the offline `verify_waitendofline` analysis.

## Addendum (2026-07-01): live `FrameDataGrab` row-orientation characterization

`examples/verify_row_orientation.py` settles the row-orientation unknown without
needing a recognizable surface feature. It runs `run_partial(max_lines=N)` (N well
below the frame's line count) in **both** directions at angle 0 and inspects which
matrix end holds the finite (scanned) rows; the rest come back NaN. Its analysis
(`classify_finite_block`, `interpret`) is pure and offline-testable (`SELFTEST`).

Run live on the `127.0.0.1:6501` rig (16-line frame, `max_lines=6`, forward
`Current (A)`):

- *up* filled matrix rows **10–15**; *down* filled matrix rows **0–5** — exactly 6
  contiguous rows each, the other 10 NaN, module idle afterward.
- Opposite matrix ends ⇒ the buffer is **physically-indexed**: matrix row index is
  a fixed physical position, so *up* vs *down* does **not** reverse row order and
  `row_order` is a single constant.
- Matrix row 0 is the frame's top edge ⇒ **`row_order = "top_to_bottom"`**. The
  Nanonis GUI confirms the underlying convention in both directions — *up* rasters
  bottom→top (rows build from the bottom edge up) and *down* rasters top→bottom
  (rows build from the top edge down) — so the result is fully confirmed.

`row_order` is a frame-*local* data-layout property: `scan_coordinate_grids` applies
it in local coordinates and then rotates by `frame.angle`, so this result is
angle-invariant. Characterizing at angle 0 keeps "up starts at the bottom edge"
unambiguous. Still uncharacterized: `column_order` (fast-axis left/right) and the
live `PropsGet` autopaste encoding.

## Next steps

Status as of 2026-07-01 (the QCoDeS scan adapter, former item 5, is now
implemented — see the QCoDeS seam section; only fast-axis `column_order` remains):

1. **Done (read-only).** `examples/characterize_m4a.py` records raw
   Piezo/Signals/Frame/Buffer/Props/Speed responses and grabs the current buffer
   forward/backward. Outputs are saved as timestamped JSON+NPZ. Orientation could
   not be read from it because the live buffer was empty (all NaN).
2. **Done (event order verified).** `examples/characterize_oneframe.py` runs one
   conservative 16x16 / 10 nm frame while recording the command sequence. The
   order is confirmed: preflight Gets -> snapshot Gets -> Frame/Buffer/Speed/Props
   Sets -> readback Gets -> `Scan.Action(Start)` -> `WaitEndOfScan` ->
   `FrameDataGrab` x N -> restore Sets, with no recovery stop and an empty
   `saved_path` (autosave off, as expected).
3. **Drafted; awaiting approval.** `examples/rig_safety_policies.py` holds a
   versioned, per-rig `ScanSafetyPolicy` seeded from the measured 3 um / 1.5 um
   piezo range and gated behind `require_approved(...)`. A qualified operator must
   review the values, set `approved=True` with a date, and bump the version.
4. **Orientation confirmed; ready to activate.**
   `scan_coordinate_grids(frame, pixels, lines, row_order=...)` produces
   controller-coordinate X/Y meshgrids using the same clockwise rotation as
   `ScanRegion.corners()`. `row_order` is a required argument with no default, so
   nothing guesses the row direction. The 2026-07-01 partial-scan characterization
   (addendum above) established **`row_order = "top_to_bottom"`** on the 6501 rig
   without needing a surface feature; pass that value. Still open: `column_order`
   (fast-axis left/right), settle when the QCoDeS adapter needs it.

## Addendum (2026-07-01): frame split into `ScanRegion`

The frame geometry — the parameters that change every shot — was factored out of
`ScanConfig` into a first-class, round-trippable `ScanRegion` (renamed from the
former effective-only `ScanFrame`, now the single frame type everywhere):

- `ScanConfig` is the **stable recipe** (channels, resolution, speed, autosave,
  restoration flags) and no longer carries `center_x/center_y/width/height/angle`.
- `ScanRegion(center_x, center_y, width, height, angle=0.0)` is the **per-shot
  target**, passed positionally: `ScanWorkflow.run(config, region)` /
  `run_partial(config, region, max_lines=...)`. `region=None` leaves the
  controller's current frame untouched (the old "leave as-is" patch semantics).
- `ScanRegion` supports the same snapshot/apply/patch idiom as `ScanSettings`:
  `ScanRegion.snapshot(client)` (read `Scan.FrameGet`), `region.apply(client)`
  (write `Scan.FrameSet`), and `region.patch(width=..., ...)` (return a modified
  copy). `ScanSettings.snapshot` reuses `ScanRegion.snapshot`; `ScanSettings.patch`
  now takes `(config, region)`.
- `ScanResult` gains `requested_region`; the QCoDeS adapter records it in provenance.

This directly sets up the atom-tracking/hyperscan loop: one fixed `config`, many
regions (`for region in tile_grid: workflow.run(config, region)`). Full suite green
(166 tests, incl. `ScanRegion` snapshot/apply/patch and region-over-snapshot patch).
