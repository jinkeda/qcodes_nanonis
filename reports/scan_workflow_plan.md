# Scan Workflow (M4) — Implementation Plan

Status: proposed (rev. 2) · Date: 2026-06-30

The second measurement vertical. Its purpose is to **prove that the shared
workflow toolkit built for bias spectroscopy is reusable** — and to surface,
deliberately, the two generalizations that a second vertical forces. The bias
spectroscopy plan is [`workflow_layer_plan.md`](workflow_layer_plan.md); what was
built is in [`workflow_layer_walkthrough.md`](workflow_layer_walkthrough.md). This
plan does **not** restate that contract — it reuses it and records only the
deltas.

> **Rev. 2 — verified against ground truth (a review round).** Protocol constants,
> field types, and Get/Set encodings below are **read from `TCPProtocol_SPM.pdf`
> pages 98–104** (not inferred); the QCoDeS 2-D axis requirement is confirmed by a
> **real temporary-database test on QCoDeS 0.54.4** (1-D setpoints raise
> `Incompatible shapes`; meshgrid setpoints succeed). `Piezo.RangeGet` confirmed
> present in the protocol but **absent from `configs/commands/Piezo.json`**. See
> the [Rev. 2 changelog](#rev-2-changelog).

## Context

`nanonis.workflows` now has a realized `spectroscopy/` vertical sitting on a
shared toolkit (`protocols`, `errors`, `state`, `models`). The QCoDeS
`ScanChannel` exposes thin frame getters/setters and `start/stop/pause/resume`,
but **nothing runs a scan end-to-end**: configure frame/buffer/props → start →
wait for completion → grab the frame data → restore state on failure. `spaik`'s
`doScan` proves the recipe is needed (position at corner, configure
frame/buffer/speed, start, wait, validate timeout, return saved file);
this plan rebuilds it on the platform, exactly as bias spectroscopy was.

## Design rules (inherited, non-negotiable)

- **Dependency direction:** `workflows.scan → CommandClient (Protocol)`. Imports
  the shared toolkit one level up (`..protocols`, `..errors`, `..state`); imports
  nothing from `nanonis.qcodes` and nothing from `qcodes`.
- **Reuse, do not re-derive.** `RestorationTransaction`, the `CommandClient` /
  `RecoverableCommandClient` protocols, the `WorkflowError` hierarchy, per-command
  `timeout=` on `send()`, `TransportState`, and `TipState` already exist and are
  contracts, not drafts.
- **Units = SI** (metres, seconds, volts), matching `configs/commands`. No pandas,
  no pickle.
- **Restore on every exit** (normal / Nanonis error / timeout /
  `KeyboardInterrupt`), best-effort, recovery-gated, aggregated into one
  `StateRestorationError` that also carries the salvaged result.
- **Returns a `ScanResult`, never a QCoDeS dataset.** Persistence is a separate
  `qcodes/` adapter that consumes the result.

## Verified protocol constants (PDF pages 98–104)

These were "confirm later" in rev. 1; they are now resolved from the manual.
Bake them in as named constants (with a regression test), **not** magic ints.

| Field | Encoding | Note |
| --- | --- | --- |
| `Scan.Action` action | `0=Start, 1=Stop, 2=Pause, 3=Resume, 4=Freeze, 5=Unfreeze, 6=GoToCenter` | uint16 |
| `Scan.Action` direction | **`1=up, 0=down`** | uint32 — **rev. 1 had this reversed** |
| `Scan.StatusGet` status | `1=running, 0=idle` | uint32 |
| `Scan.WaitEndOfScan` timeout_status | `1=timed-out, 0=completed` | uint32 |
| `Scan.FrameDataGrab` data_direction (arg) | `1=forward, 0=backward` | uint32 |
| `Scan.FrameDataGrab` scan_direction (resp) | `1=up, 0=down` | uint32 |
| `Scan.FrameSet` | **exactly 5×float32** (Center X, Center Y, Width, Height, Angle) | **no wait flag** (rev. 1 guessed one) |

**Still genuinely unknown (needs read-only live hardware, M4-A):** the **row/column
orientation** of `FrameDataGrab` output and whether an *up* vs *down* scan flips
row order. Rotation is **not** the unknown (see QCoDeS persistence).

## What is reused vs. new

| Concern | Reused as-is | New for scan |
| --- | --- | --- |
| Command protocols | `CommandClient`, `RecoverableCommandClient` | — |
| Transaction | `RestorationTransaction`, `RecoveryReport`* | *needs G1 rename (below) |
| Errors | `WorkflowError`, `StateRestorationError`, `SafetyPreflightError`, `RecoveryError` | `ScanResponseError`, `ScanTimeoutError` |
| Transport | per-command `timeout`, `TransportState`, `reconnect()` | — |
| Tip state | `TipState` (feedback/bias/setpoint) | reused unchanged, optional participant |
| Recovery helper | — | **generalized** `recover_module(...)` (G1) |
| Safety policy | the *injection pattern* | **generalized** `TipRestorePolicy` (G2) + `ScanSafetyPolicy` |
| Config / settings | the snapshot-and-patch pattern | `ScanConfig`, `ScanSettings` + Get/Set conversions |
| Result | the own-and-freeze immutability pattern | `ScanResult` (2-D, per channel/direction) |
| QCoDeS adapter | — | **deferred — stub API only** (see below) |

## The two generalizations this vertical forces

These are the *point* of M4. Do them as small, test-backed refactors of the
shared toolkit — not by copying spectroscopy code into `scan/`.

### G1 — Generic module recovery

`recover_bias_spectroscopy()` is hard-wired to `BiasSpectr.Stop` /
`BiasSpectr.StatusGet`, and **`RecoveryReport` is still spectroscopy-specific**:
its field is `spectroscopy_stopped` ([`state.py:25`](../src/nanonis/workflows/state.py))
and `_recovery_error` hard-codes the text *"BiasSpectr stop was not confirmed"*.
G1 therefore must:

1. Extract a parameterized helper in `state.py`:

   ```python
   def recover_module(client, *, stop, status_stopped, timeout, poll_interval=0.1):
       # stop: Callable[[CommandClient], None]
       # status_stopped: Callable[[CommandClient], bool]
       ...  # reconnect → query stopped → stop → monotonic bounded poll → RecoveryReport
   ```

2. **Rename `RecoveryReport.spectroscopy_stopped → module_stopped`** (keep a
   `spectroscopy_stopped` read-only compatibility property so the spectroscopy
   tests stay green), and **generalize the error text** ("module stop was not
   confirmed").
3. **Resolve `record_recovery(origin=...)`.** Its signature is `origin:
   BaseException` (non-optional) ([`state.py:205`](../src/nanonis/workflows/state.py)),
   so the rev. 1 `origin=None` call is a type error. Make it
   `origin: BaseException | None = None`.

`recover_bias_spectroscopy` becomes a thin partial of `recover_module`;
`recover_scan` is another partial. Second-interrupt / unconfirmed-stop /
failed-reconnect semantics are unchanged.

### G2 — Generalize the tip-restore policy

`TipState.restore(client, safety_policy)` currently takes
`BiasSpectroscopySafetyPolicy`, but `TipState` is generic and scanning also moves
the tip. Extract the bias-restore fields into a shared, vertical-neutral policy:

```python
# workflows/models.py (shared)  — or workflows/policies.py once it lands
@dataclass(frozen=True)
class TipRestorePolicy:
    bias_restore_mode: BiasRestoreMode
    bias_ramp: BiasRampPolicy | None
    allow_zero_crossing: bool
    feedback_off_during_restore: bool = True
    external_bias_restorer: ExternalBiasRestorer | None = None
```

`BiasSpectroscopySafetyPolicy` keeps its current fields but composes a
`TipRestorePolicy` (e.g. a `.tip` property), so `TipState.restore` depends only on
the shared type. **Back-compat:** keep `BiasSpectroscopySafetyPolicy`'s existing
constructor signature working; the spectroscopy tests are the regression gate. Do
**not** build a standalone `safety/` layer — only the shared *policy type* moves;
preflight *mechanism* stays per-vertical.

## Schema gaps (M4-A — blocking, the "M0A" of scan)

Field order/types below are **read from the PDF** (pages cited). Add to
`configs/commands/*.json` and guard with `tests/test_schema.py`.

- **`Scan.FrameSet`** (p.99) — *currently missing and already called* by
  [`scan.py:115`](../src/nanonis/qcodes/channels/scan.py) and
  [`proxies.py:71`](../src/nanonis/command/proxies.py); those calls decode-fail
  today. Exactly **5 float32**: `Center X, Center Y, Width, Height, Angle`. **No
  wait flag.**
- **`Scan.SpeedSet`** (p.103) — `Forward linear speed (f), Backward linear speed
  (f), Forward time per line (f), Backward time per line (f), Keep parameter
  constant (H), Speed ratio (f)`. **`Scan.SpeedGet`** returns the same six.
- **`Piezo.RangeGet`** (p.91) — `Range X (f), Range Y (f), Range Z (f)`. Present in
  the protocol, **absent from `Piezo.json`**; mandatory preflight cannot work
  without it. Add it here.
- **Correct `Scan.BufferGet`** — `Pixels` and `Lines` are **signed `int` (i)**, not
  `uint32 (I)` (p.100). (`BufferSet` already uses `i`.)

### Get/Set encodings are asymmetric — add conversion functions

`Scan.PropsGet` and `Scan.PropsSet` (and `SpeedGet`/`SpeedSet`) **do not share an
encoding**, so snapshot-and-restore cannot feed Get values back into Set. M4-A
adds small, tested conversion functions:

| Field | `*Get` (read) | `*Set` (write) |
| --- | --- | --- |
| Continuous scan | `0=Off, 1=On` | `0=no-change, 1=On, 2=Off` |
| Bouncy scan | `0=Off, 1=On` | `0=no-change, 1=On, 2=Off` |
| Autosave | `0=All, 1=Next, 2=Off` | `0=no-change, 1=All, 2=Next, 3=Off` |
| Autopaste | (enum; confirm on hardware) | `0=no-change, 1=All, 2=Next, 3=Off` |
| Speed keep-constant | `0=linear speed, 1=time per line` | `0=no-change, 1=linear, 2=time` |

So restoring a snapshot means re-encoding every one of these — a plain echo would
silently change the controller's mode.

Already present and usable: `Scan.Action`, `Scan.StatusGet`, `Scan.WaitEndOfScan`
(returns the saved **file path** — unlike `BiasSpectr.Start`), `Scan.WaitEndOfLine`,
`Scan.FrameGet`, `Scan.PropsGet/Set`, `Scan.BufferSet`, `Scan.FrameDataGrab`.

## File layout

```text
src/nanonis/workflows/scan/
├── __init__.py            # public scan API (re-exported by workflows/__init__)
├── models.py             # ScanConfig, ScanSettings, ScanSpeed, ScanProps (+ Get/Set conversions)
├── result.py             # ScanResult, ScanChannelImage, normalization
└── workflow.py           # ScanWorkflow, preflight, duration estimate, recover_scan, factory
src/nanonis/workflows/
├── state.py              # recover_module + RecoveryReport.module_stopped (G1)
└── models.py             # + TipRestorePolicy (G2)
src/nanonis/qcodes/
└── scan.py               # register_scan_result() + add_scan_result()  (M4-D)
tests/workflows/scan/
├── conftest.py           # reuse FakeController; scripted Scan.* responses
├── test_models.py        # incl. Get/Set conversion round-trips
├── test_result.py
└── test_scan.py
```

## ScanConfig — snapshot-and-patch

Optional fields are `None` = "leave current value as-is"; structural validation is
I/O-free and runs before any command is sent.

```python
@dataclass(frozen=True)
class ScanConfig:
    channel_indexes: tuple[int, ...]
    direction: Literal["up", "down"] = "up"
    # frame (None = keep current frame field)
    center_x: float | None = None        # m
    center_y: float | None = None        # m
    width: float | None = None           # m
    height: float | None = None          # m
    angle: float | None = None           # deg (positive = clockwise, per PDF)
    # buffer
    pixels: int | None = None
    lines: int | None = None
    # speed (None = keep)
    forward_line_time: float | None = None    # s/line
    backward_line_time: float | None = None   # s/line
    speed_ratio: float | None = None
    # props
    autosave: Literal["all", "next", "off"] | None = None   # NOT a bool — enum
    series_name: str | None = None
    comment: str | None = None
    # acquisition
    data_directions: tuple[Literal["forward", "backward"], ...] = ("forward",)
    grab_data: bool = True               # FrameDataGrab after WaitEndOfScan
    acquisition_timeout: float | None = None   # s; None = computed bound
    recovery_timeout: float = 15.0
    status_poll_interval: float = 0.1
    restore_state: bool = True
    restore_tip_state: bool = False      # scans usually keep tunnel conditions
```

`__post_init__` validates: ≥1 unique non-negative channel; `pixels`/`lines` ≥ 2
when provided; `width`/`height` finite and > 0 when provided; `angle` finite;
line times finite and > 0; recovery-timing as in spectroscopy.

**Continuous scan is not a user field.** A continuous scan never reaches a
`WaitEndOfScan` completion, so this one-shot workflow **forces continuous off
internally** (sends `Continuous = Off` in `apply`) and restores the original mode
on exit. It is intentionally not exposed for snapshot-and-patch; that omission is
documented here.

`ScanSettings.snapshot(client)` reads `FrameGet` + `BufferGet` + `PropsGet` +
`SpeedGet` (decoding every Get-encoded enum into a semantic value). `.patch(config)`
applies non-`None` fields. `.apply(client)` / `.restore(client)` **re-encode**
every prop/speed enum through the Set conversions and send complete
`FrameSet`/`BufferSet`/`PropsSet`/`SpeedSet` argument lists in a lab-defined order
(frame → buffer → speed → props), best effort, returning `{field: exc}`.

**Preserve the full `PropsGet` state**, not just autosave: `bouncy`, `autopaste`,
`series_name`, `comment`, `modules_names`, and the parameter-header table are all
snapshotted and restored (bouncy/autopaste via the tri-state Set conversion;
modules/parameters round-tripped verbatim). The workflow changes only what
`config` overrides.

## Acquisition model

One frame, acquire-first. Recovery is **not** limited to transport errors: any
post-start failure with completion unconfirmed must stop-and-confirm the scanner
before restoration runs.

```python
preflight(client, config, policy) unless unsafe_skip_preflight
with RestorationTransaction(client) as tx:
    if config.restore_tip_state:
        tx.preserve("tip", TipState.snapshot(client),
                    restorer=lambda s: s.restore(client, policy.tip))
    original = tx.preserve("scan", ScanSettings.snapshot(client))
    original.patch(config).apply(client)            # forces continuous OFF; re-encodes enums
    effective = ScanSettings.snapshot(client)        # authoritative readback
    started = utcnow(); t0 = monotonic()
    start_attempted = completed = False
    try:
        start_attempted = True
        client.send("Scan.Action", ACTION_START,
                    DIRECTION_UP if config.direction == "up" else DIRECTION_DOWN)  # up=1, down=0
        wait = client.send("Scan.WaitEndOfScan", nanonis_timeout_ms(config, effective),
                           timeout=resolve_acquisition_timeout(config, effective))
        if wait.timeout_status == 1:                 # 1 = timed out (PDF)
            raise ScanTimeoutError(...)
        completed = True
    except BaseException as exc:                      # transport, Nanonis error, timeout, interrupt
        if start_attempted and not completed:         # scanner may still be running
            tx.record_recovery(recover_scan(client, timeout=config.recovery_timeout,
                               poll_interval=config.status_poll_interval), origin=exc)
        raise
    images = grab_frame(client, effective, config) if config.grab_data else ()
    result = normalize_scan(images, saved_path=wait.file_path, config=config,
                            effective=effective, started=started, duration=monotonic()-t0)
    tx.attach_result(result)
return result
```

`grab_frame` calls `Scan.FrameDataGrab(channel_index, data_direction)` (forward=1,
backward=0) for each requested channel × direction, validates `rows == lines` and
`cols == pixels` (warn, don't assert), and keeps `scan_direction` from the
response. A transport failure during `grab_frame` (after completion) leaves the
scanner stopped, so the transaction's existing `DESYNCHRONIZED` gate blocks
restoration writes without a second stop.

**Two timeouts, distinct.** `Scan.WaitEndOfScan` takes a **Nanonis-side**
`timeout_ms`; the **socket** per-command timeout must exceed it. The raster always
sweeps forward **and** backward per line regardless of which directions are
*saved*, so:

```python
fwd = effective.speed.forward_time_per_line
bwd = effective.speed.backward_time_per_line
raster = lines * (fwd + bwd)                          # NOT * len(data_directions)
estimate = raster + positioning_margin                # corner move + settling
nanonis_timeout_ms = estimate * 1000 + margin_ms
socket_timeout = max(estimate, nanonis_timeout_ms / 1000) * 1.5 + 5
```

Guard zero/non-finite line times like the slew-rate ÷0 guard. Record both
`estimated_acquisition_duration` and `acquisition_timeout_used` on the result.
(Rev. 1 used `lines × forward_line_time × len(directions)`, which both ignored the
backward raster pass and wrongly scaled by saved directions — roughly half the
true time for a symmetric line: e.g. ~51.2 ms each way.)

## Recovery contract

`recover_scan = recover_module(client, stop=lambda c: c.send("Scan.Action",
ACTION_STOP, 0), status_stopped=lambda c: int(c.send("Scan.StatusGet")) == 0, ...)`
(`ACTION_STOP = 1`; idle = StatusGet 0). Same gate as spectroscopy: restoration
writes only when `RecoveryReport.restoration_allowed` (`transport_ready and
module_stopped is True`). Pause/resume are **not** recovery actions — only
stop-and-confirm is.

## ScanResult — 2-D, immutable

```python
@dataclass(frozen=True)
class ScanChannelImage:
    name: str
    channel_index: int
    direction: Literal["forward", "backward"]
    data: FloatArray            # (lines, pixels), owned + frozen in __post_init__

@dataclass(frozen=True)
class ScanResult:
    images: tuple[ScanChannelImage, ...]
    frame: ScanFrame            # center/width/height/angle → physical grids
    requested_config: ScanConfig
    effective_settings: ScanSettings
    saved_path: str             # from WaitEndOfScan — real, unlike spectroscopy
    acquisition_started_at: datetime    # tz-aware UTC
    acquisition_finished_at: datetime
    acquisition_duration: float
    estimated_acquisition_duration: float
    acquisition_timeout_used: float
```

Same invariants as `BiasSpectroscopyResult`: own + freeze every array in
`__post_init__`; validate declared rows/cols vs. shape; tz-aware timestamps;
duration ≥ 0; finish ≥ start. `NaNPolicy` (reuse the existing enum + helpers) over
the stacked image data. `(lines, pixels)` confirmed by `Scan.BufferGet`;
forward/backward kept distinct, never inferred.

## QCoDeS persistence (M4-D) — DEFERRED, stub API only

**Decision (current stage): do not implement QCoDeS persistence for scan now.**
The real deliverable is the self-describing `ScanResult`; persisting it to QCoDeS
is a later concern and should not absorb effort at this stage. Ship only a
signature-only stub so the seam exists:

```python
# nanonis/qcodes/scan.py
def register_scan_result(experiment, result, *, station=None):
    """Deferred. Register a ScanResult's schema with QCoDeS. Not yet implemented."""
    raise NotImplementedError("scan QCoDeS persistence is deferred; see scan_workflow_plan.md")

def add_scan_result(datasaver, registered, result):
    """Deferred. Insert a ScanResult into a QCoDeS run. Not yet implemented."""
    raise NotImplementedError("scan QCoDeS persistence is deferred; see scan_workflow_plan.md")
```

> **Recorded finding (so the future implementation doesn't re-discover it):**
> QCoDeS 0.54.4 requires each 2-D image's setpoints to be **2-D meshgrids of the
> same `(lines, pixels)` shape** — a 1-D `x_pixel`/`y_line` axis is rejected
> (`Incompatible shapes`), confirmed by a temporary-DB test. When resumed:
> mandatory index meshgrids (`np.meshgrid(arange(pixels), arange(lines))`);
> physical `x_m`/`y_m` grids work for *any* angle (rotation is a coordinate
> transform, not the blocker) but are gated on row/column orientation; independent
> setpoints only; sanitized ids; provenance + `saved_path` + `frame`.

## Preflight (mandatory unless `unsafe_skip_preflight`)

Fail-closed, bounds from an injected `ScanSafetyPolicy`:

- **Frame within piezo range** — `Piezo.RangeGet` returns total X/Y/Z range (m).
  Treat usable travel as `±range/2` about centre and require all four (rotated)
  frame corners to fit, minus a policy safety margin. Unknown/zero range → raise.
- **Channels exist** — each index `< len(Signals.NamesGet())` (PDF caps at 0..127).
- **Buffer within policy maxima** — `BufferGet` returns the **current** pixels/lines,
  **not** controller maxima, so `max_pixels` / `max_lines` live in
  `ScanSafetyPolicy`; require `> 0` and `≤` those.
- **Speed within policy** — line time / speed within `[min, max]`.
- **Not already scanning** — `Scan.StatusGet == 0`.

Keep scan's validators in `scan/workflow.py` until a third vertical proves a shared
`safety` module is warranted.

## Testing plan (`FakeController`, no socket/QCoDeS/DB; logic tier)

| Test | Asserts |
| --- | --- |
| `test_state.py::recover_module_generic` | `recover_module` reconnect→query→stop→poll; `recover_bias_spectroscopy` still passes (regression) |
| `::recovery_report_module_stopped_alias` | `module_stopped` field + `spectroscopy_stopped` compat property; `record_recovery(origin=None)` accepted |
| `test_models.py::tip_restore_policy_shared` | `TipState.restore` takes `TipRestorePolicy`; `BiasSpectroscopySafetyPolicy` back-compat unbroken |
| `::props_speed_get_set_conversions` | continuous/bouncy/autosave/autopaste + speed selector round-trip Get→semantic→Set correctly (incl. no-change) |
| `::autosave_is_enum` | `autosave` accepts `"all"/"next"/"off"/None`, rejects bool |
| `test_scan.py::invalid_config_sends_nothing` | bad config (pixels<2, dup channel) → zero sends |
| `::continuous_forced_off` | `apply` sends Continuous=Off; original mode restored on exit |
| `::snapshot_patch_readback_order` | FrameGet/BufferGet/PropsGet/SpeedGet → Set in frame→buffer→speed→props order → readback |
| `::none_overrides_preserve_existing` | `None` fields reuse snapshot, not 0.0 |
| `::direction_constant_up_is_1` | `direction="up"` sends 1, `"down"` sends 0 |
| `::nanonis_error_midwait_triggers_recovery` | a **Nanonis command error** during WaitEndOfScan → `recover_scan` runs (not just transport errors) |
| `::nanonis_timeout_triggers_recover_then_raises` | `timeout_status==1` → recover, `ScanTimeoutError`, no restore writes if not stopped |
| `::transport_error_triggers_recovery` | reset/partial/protocol error → recovery, then gated restore |
| `::two_timeouts_and_duration` | socket timeout > Nanonis `timeout_ms`; estimate uses fwd+bwd line time; zero line-time → warning, no div0 |
| `::frame_data_grab_per_channel_direction` | grabs each channel×direction (fwd=1,bwd=0); rows/cols mismatch warns |
| `::saved_path_from_wait` | `result.saved_path` == `WaitEndOfScan` file path |
| `::restoration_error_carries_result` | scan completes, restore fails → `StateRestorationError.result` set |
| `test_result.py::image_owned_and_frozen` | 2-D arrays copied + read-only on direct construction |
| `::backward_direction_explicit` | forward/backward images kept distinct, not inferred |
| `test_schema.py::scan_setters_field_counts` | `FrameSet`(5×f), `SpeedSet/Get`(4f+H+f), `BufferGet` pixels/lines `i`, `Piezo.RangeGet`(3×f) |
| `test_qcodes::scan_stub_raises` | the deferred `register_scan_result` / `add_scan_result` stubs raise `NotImplementedError` |

(The full meshgrid-axis QCoDeS tests are deferred with M4-D.)

## Milestones

- **M4-A — schemas, encodings, and read-only characterization (blocking).**
  1. Add/correct schemas: `Scan.FrameSet` (5×f, no flag), `Scan.SpeedSet`/`SpeedGet`,
     `Piezo.RangeGet`, and fix `Scan.BufferGet` pixels/lines to `i`; schema
     regression tests; add to the live-test selection. Fixes the already-broken
     `FrameSet` call path.
  2. Wire-value enums + Get/Set conversion functions (props, speed) with round-trip
     tests.
  3. **Read-only live-hardware characterization** (real socket, getters only): row/
     column orientation of `FrameDataGrab`, up-vs-down row order, autopaste Get
     encoding, `FrameGet`/`BufferGet`/`SpeedGet`/`PropsGet` field alignment.

  (QCoDeS work is **not** part of M4-A — see deferred M4-D.)
- **M4-B — toolkit generalizations (G1 + G2).** `recover_module`,
  `RecoveryReport.module_stopped` (+ compat), `record_recovery(origin=None)`, and
  `TipRestorePolicy`, each landed with the spectroscopy regression suite green.
  Pure-Python, `FakeController`.
- **M4-C — scan vertical.** `scan/models.py`, `result.py`, `workflow.py`:
  snapshot/patch/readback with conversions, continuous forced off, start→wait→grab,
  broadened recovery, two-timeout + fwd+bwd duration, mandatory preflight, lossless
  2-D result. Validated on **real hardware over a real socket** (not a simulator).
- **M4-D — QCoDeS persistence (DEFERRED).** Ship only the signature-only stub
  (`register_scan_result` / `add_scan_result` raising `NotImplementedError`). Full
  implementation — acquire-first, 2-D meshgrid axes, provenance — is postponed; do
  not invest effort at this stage. The recorded meshgrid finding above is the
  starting point when resumed.

## Open decisions

- **Continuous / line-by-line acquisition** — this plan does one frame via
  `WaitEndOfScan`. A streaming `WaitEndOfLine` variant (live preview, incremental
  persistence — the atom-tracking/hyperscan precursor) is deferred; decide if M4
  needs it or if one-shot is the honest first vertical.
- **Row/column orientation** — does `FrameDataGrab` return rows top→bottom, and
  does an *up* vs *down* scan flip row order? This gates physical-coordinate grids
  (rotation does not). Characterize read-only on hardware in M4-A.
- **Tip-state restoration default** — scans normally keep tunnel conditions
  (`restore_tip_state=False`); confirm with the lab whether any scan path should
  snapshot/restore bias/setpoint/feedback.
- **`ScanSafetyPolicy` contents** — `max_pixels`/`max_lines`, piezo safety margin,
  speed min/max, and how rotated corners are checked against `±range/2` — per-rig,
  confirm with the lab.
- **Autopaste Get encoding** — the PDF's `PropsGet` autopaste text mirrors the Set
  "no-change" wording (likely a manual copy-paste); confirm the real read encoding
  on hardware before relying on autopaste restoration.

## Reference: scan command schemas (verified against the PDF)

- `Scan.Action(action H, direction I)` — action `0=start,1=stop,2=pause,3=resume,
  4=freeze,5=unfreeze,6=center`; direction **`1=up, 0=down`**.
- `Scan.StatusGet() -> status I` — `1=running, 0=idle`.
- `Scan.WaitEndOfScan(timeout_ms i) -> (timeout_status I, file_path_size I, file_path s)`
  — `timeout_status 1=timed-out, 0=completed`; `timeout_ms = -1` waits forever.
- `Scan.WaitEndOfLine(timeout_ms i) -> (timeout_status I, line_number i, movement H, pass i)`
  — movement `0=fwd,1=bwd,2=to-center,3=to-start`.
- `Scan.FrameSet(center_x f, center_y f, width f, height f, angle f)` — **5×f, no flag.**
- `Scan.FrameGet() -> (center_x, center_y, width, height, angle : f)`.
- `Scan.BufferSet(num_channels i, channel_indexes 1Dint, pixels i, lines i)` /
  `Scan.BufferGet() -> (num_channels i, channel_indexes 1Dint, pixels i, lines i)`
  (**pixels/lines are signed `i`**).
- `Scan.PropsSet(continuous I, bouncy I, autosave I, series_name s, comment s,
  modules_names_size i, modules_names_number i, modules_names 1Dstr, autopaste I)`
  — set-side enums are tri-state (`0=no-change`); see conversion table.
- `Scan.PropsGet()` — read-side enums differ (`continuous/bouncy 0=Off/1=On`,
  `autosave 0=All/1=Next/2=Off`) + per-module parameter table.
- `Scan.SpeedSet(fwd_speed f, bwd_speed f, fwd_time f, bwd_time f, keep_const H,
  speed_ratio f)` / `Scan.SpeedGet()` — `keep_const` Set `0=no-change,1=linear,
  2=time`; Get `0=linear,1=time`.
- `Scan.FrameDataGrab(channel_index I, data_direction I) -> (name s, rows i, cols i,
  data 2Dfloat32, scan_direction I)` — arg `data_direction 1=fwd,0=bwd`; resp
  `scan_direction 1=up,0=down`.
- `Piezo.RangeGet() -> (range_x f, range_y f, range_z f)` — total range per axis;
  **add to `Piezo.json`.**

## Rev. 2 changelog

Accepted from a verification review; every claim checked against ground truth:

- **QCoDeS persistence DEFERRED (priority decision).** Per the current-stage
  decision, scan QCoDeS persistence (M4-D) is a **signature-only stub**, not real
  work — the `ScanResult` is the deliverable. The living-test finding is recorded
  for later: 1-D setpoints raise `Incompatible shapes` on QCoDeS 0.54.4 while
  meshgrid `(lines, pixels)` setpoints succeed; physical grids gated on orientation,
  not `angle == 0`. The existing spectroscopy QCoDeS adapter (M3) is untouched.
- **Recovery broadened (blocking).** Recover on **any** post-start failure with
  completion unconfirmed (Nanonis command errors included), via
  `start_attempted`/`completed` tracking — not only transport errors/interrupts.
- **Duration estimate corrected (blocking).** `lines × (fwd + bwd line time) +
  positioning margin`; saved data directions don't scale raster time.
- **Protocol constants (PDF-verified).** `Action` direction was **reversed** (1=up,
  0=down); StatusGet 1=running; WaitEndOfScan 1=timed-out; FrameDataGrab 1=fwd;
  `FrameSet` is 5×f with **no wait flag**.
- **Schema/model.** Add `Piezo.RangeGet`; fix `BufferGet` pixels/lines to `i`;
  `autosave` is an enum (`all/next/off`), not bool; add **Get/Set conversion
  functions** (props + speed) because the encodings are asymmetric; preserve
  bouncy/autopaste/modules/parameter-header; force `continuous` off internally.
- **G1.** Rename `RecoveryReport.spectroscopy_stopped → module_stopped` (compat
  property), generalize the recovery error text, make `record_recovery` `origin`
  optional.
- **Safety.** `max_pixels`/`max_lines` belong in `ScanSafetyPolicy` (BufferGet is
  current, not maxima); define `Piezo.RangeGet` as `±range/2` + margin + rotated
  corner checks.
- **Milestones.** M4-A expanded to: corrected schemas + wire-value enums/conversions
  + read-only live-hardware characterization + real QCoDeS meshgrid test.
