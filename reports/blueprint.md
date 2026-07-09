# Blueprint — What to Adopt from `spaik`

Status: strategic blueprint · Date: 2026-07-02 (datalog + drift-compensation
verticals planned as M5; session/rig-config policy decided; previously: scan +
data-readers verticals moved to Realized, shared `geometry`/`types` primitives
extracted)

## Guiding principle

Treat **`spaik`** as a *catalogue of proven experimental recipes and domain
requirements* — not as a codebase to copy. `spaik`'s `SPMMeasurement` is a
~7,000-line god-object mixing hardware control, pandas configs, pickle I/O,
device drivers, and plotting, with state restoration in an unprotected
`finally`. The recipes it encodes are valuable; its structure is not.

Treat **this repository** as the clean platform on which those recipes are
rebuilt: a `protocol → command` core, with `workflows` (transactional measurement
recipes) and `qcodes` (optional adapters) as **parallel** consumers of the
command layer. The rule is **small workflow services, not a second
`SPMMeasurement` god class.**

This document is the high-level vision and backlog. The concrete, review-hardened
design for the first vertical lives in
[`workflow_layer_plan.md`](workflow_layer_plan.md); what has actually been built
is recorded in [`workflow_layer_walkthrough.md`](workflow_layer_walkthrough.md).

## Target architecture

`workflows` and `qcodes` are **parallel** consumers of the command layer, not a
stack. Both build on the command client; neither builds on the other. QCoDeS is
an *optional adapter*: its instrument channels use the command layer directly,
and its persistence adapters consume **completed workflow results** — core
workflows never create or return QCoDeS datasets.

```text
      geometry/ + types/             # neutral value types: FrameGeometry, RowOrder/
               ▲                     #   ColumnOrder, scan_coordinate_grids, NaNPolicy
               │  (imported downward by workflows/ AND data/ — no sideways deps)
            protocol/                 # TCP transport + exceptions + TransportState
               ▲
            command/                  # registry, encoder/decoder, controller
               ├──────────────┐
               ▼              ▼
          workflows/      qcodes/ instrument + channels
               │ returns       ▲ consume results
               ▼               │
          domain results ──────┘ → qcodes/ persistence adapters → QCoDeS datasets

          data/ readers → domain data → optional xarray / qcodes/ adapters   # realized
```

```text
nanonis/
  protocol/                  # exists
  command/                   # exists

  geometry.py                # neutral: FrameGeometry, RowOrder/ColumnOrder, scan_coordinate_grids
  types.py                   # neutral: NaNPolicy (shared by workflows/ and data/)

  workflows/                 # transactional measurement recipes (spectroscopy + scan realized)
    protocols.py             #   CommandClient, RecoverableCommandClient
    errors.py                #   WorkflowError hierarchy
    state.py                 #   RestorationTransaction, TipState, recover_module
    models.py                #   shared TipRestorePolicy (policies.py not yet needed)
    cancellation.py          #   CancelToken + progress events (planned — M5a prerequisite)
    spectroscopy/            #   bias spectroscopy (implemented + live-validated)
    scan/                    #   full scan workflow (implemented; run + run_partial)
      models.py              #     ScanRegion now composes geometry.FrameGeometry
      geometry.py            #     compat re-export of nanonis.geometry
    tunnel/                  #   prepare/restore tunnelling conditions
    datalog/                 #   time-trace acquisition (planned, M5a — polling backend first)
    drift/                   #   drift compensation (planned, M5b sync + M6 background)
    atom_tracking/           #   stub — backlog (needs checkpoint/resume first)

  qcodes/                    # optional adapter (exists)
    instrument.py
    spectroscopy.py          #   persistence adapter: result -> QCoDeS dataset
    scan.py
    data.py                  #   file-domain -> QCoDeS dataset (sxm/3ds/dat)

  data/                      # STM data models + readers (REALIZED; hardware-free leaf)
    models.py                #   SxmData, Grid3DData, DatData, SessionConfig (immutable, typed)
    validation.py            #   I/O-free NaNPolicy handling
    transforms.py            #   independent, opt-in, NaN-safe background corrections
    readers/                 #   sxm.py, three_ds.py, dat.py, session.py (+ nanonispy boundary)
    adapters/                #   xarray.py  (a data->QCoDeS adapter lives in qcodes/data.py)
```

**Dependency direction (non-negotiable):** `workflows -> command API + the
protocol layer's stable error/state types` (`NanonisTimeoutError`,
`NanonisConnectionError`, `NanonisProtocolError`, `TransportState`). Those are the
protocol layer's public contract, so depending on them is allowed and is stated
here explicitly. The workflow package imports nothing from `nanonis.qcodes` and
nothing from `qcodes`. Units are volts / SI, matching `configs/commands`. No
pandas, no pickle in this layer.

**Neutral primitives (`nanonis.geometry`, `nanonis.types`).** `workflows/` and
`data/` are parallel leaves that share value types (frame geometry, orientation
literals, `NaNPolicy`). Rather than one importing the other (a sideways dependency)
or each cloning the types (drifting conventions), both import **downward** from a
bottom-level `geometry`/`types` layer that depends on nothing. `data/` therefore
imports **only** these neutral modules — nothing from `command`, `protocol`,
`workflows`, or `qcodes` — and controls no hardware. `ScanRegion` composes
`FrameGeometry` (keeping its hardware `snapshot/apply/patch`), so there is one
rotation convention and one orientation vocabulary across acquired and read frames.

> `policies.py` does **not** exist yet — it appears when the scan vertical needs
> to share tip restoration (the `TipRestorePolicy` / bias-ramp generalization in
> [`scan_workflow_plan.md`](scan_workflow_plan.md), G2). Until then those fields
> live on `BiasSpectroscopySafetyPolicy`.

### Subsystem responsibilities

- **`workflows/tunnel/`** — reusable procedures for preparing and restoring
  tunnelling conditions: read bias / current setpoint / feedback state; ramp bias
  and current setpoint; enable/disable Z feedback safely; wait for current/Z
  stabilization; restore initial tunnel conditions; optionally withdraw or hold
  the tip before risky operations.
- **`workflows/scan/`** — the useful sequence from `doScan`: position at the
  correct corner, configure frame/buffer/speed, start, wait, validate timeout,
  and return a `ScanResult` (owning the frame data, and the saved-file paths the
  controller reports). It returns a domain result, **never** a QCoDeS dataset —
  persisting it is a separate `qcodes/` adapter.
- **`workflows/datalog/`** (planned, M5a) — time-trace acquisition: a typed
  `TimeTraceConfig` (duration, channels, sample interval) and an immutable
  `TimeTraceResult` (monotonic-anchored timestamps, per-channel arrays,
  provenance — never a filename as a time base). The first backend **polls**
  the Signals module (add `Signals.ValsGet` to `configs/commands` so one sample
  is one round-trip): drift is a pm/s phenomenon, so 5–20 Hz over 60–300 s is
  sufficient and needs no new socket. **Deferred backends:** TCPLog streaming
  (schema corrected 2026-07-02 — `ChsSet` was missing and its args were on
  `Stop` — but the group has never been live-validated, and its data arrives on
  a **separate stream port** requiring a second reader socket) and the
  file-based Nanonis Data Logger module (`spaik`'s `doDataLogging` path, with
  its sleep-and-reread settling problem). Neither is needed for drift.
- **`workflows/drift/`** (planned, M5b/M6) — the drift-compensation recipe from
  `spaik`'s notebook, rebuilt. This is the flagship **GUI-impossible**
  capability: the Nanonis GUI applies a *constant* drift velocity, while the
  fitted model feeds forward the physically correct *decaying* rate for
  post-approach creep. Fit a `TimeTraceResult` with a pure, I/O-free
  `DriftModel` protocol (`LogDriftModel` first — `fitting.py` is CI-testable on
  synthetic data), then write the fitted rate to `Piezo.DriftCompSet` (already
  in `configs/commands`). The controller applies the velocity in hardware;
  Python only *updates* it every 1–10 s (`spaik`'s 10 Hz loop was ~100×
  overkill). Design rules learned from `spaik`'s defects: exit is an explicit
  reason enum (`CONVERGED` / `MAX_DURATION` / `FIT_DIVERGED` / `CANCELLED` /
  `RATE_LIMIT_EXCEEDED`), so the inverted-condition bug in
  `spaik.driftCompensation` cannot be written; rates above the policy limit are
  **clamped and reported**, never a silent `break`; the prior
  `Piezo.DriftCompGet` state is a transaction participant with an explicit
  `on_exit` policy (`ZERO_AND_ON` vs `RESTORE_PRIOR`), not an accident of a
  `finally` block; the time base is monotonic, anchored to the trace's
  `started_at` — never parsed from a filename.
- **`data/`** (realized) — STM data models, Nanonis file readers (`sxm`,
  `three_ds`, `dat`, `session`), transforms, and `validation`. It must **not**
  control hardware, and imports only the neutral `geometry`/`types` primitives.
  Readers produce immutable **domain data** (raw order preserved); optional adapters
  turn that into xarray objects or QCoDeS datasets (the data→QCoDeS adapter lives in
  `qcodes/data.py`, orientation applied there). Built on released `nanonispy` behind
  a parser boundary; transforms are opt-in and never applied by a reader.

> **Design note — no separate `safety/` package.** The original sketch proposed a
> top-level `safety/` (policies, preflight, ramping, errors). The realized design
> instead *injects* a typed, rig-specific `BiasSpectroscopySafetyPolicy` into each
> workflow, with preflight and ramp policy living next to the workflow that uses
> them. This keeps safety rules reviewable and per-rig without creating a second
> quasi-god service. Treat safety as a **cross-cutting concern injected into
> workflows**, not a standalone subsystem.

## Cross-cutting requirements

Every workflow must satisfy these, regardless of which recipe it implements.

> **Canonical vertical shape.** The two realized hardware verticals both follow one
> pipeline, and it is the template for the next one:
>
> **typed config (validated, I/O-free)** → **injected safety policy (preflight)** →
> **transactional run (snapshot → acquire → recovery-gated best-effort restore)** →
> **immutable, validated result (+ provenance)**.
>
> The subsections below detail each stage; the ordering *is* the point (config is
> validated before any command; preflight runs before the transaction opens; the
> result is frozen after). Safety is an *injected* cross-cutting concern, not a
> stage that owns the run (see the design note above — no standalone `safety/`).
> The read-only `data/` vertical is the **reduced** form of this shape —
> `typed args → parse → validate → immutable result (+ provenance)` — with no
> policy and no transaction, because it touches no hardware.

### State transactions

**Invariant:** every mutable hardware state a workflow *owns or modifies* must
have an explicit snapshot, a restoration policy, and a failure-reporting path. A
workflow snapshots only what it touches — a spectroscopy workflow does **not**
snapshot the scan frame unless it changes it.

Restoration is **not guaranteed** — it cannot be after a lost connection, failed
reconnect, second interrupt, or unconfirmed-stopped module. The honest contract:
restoration is *attempted* in reverse order **when recovery confirms writes are
safe**; it covers normal exit, Nanonis error, timeout, and `KeyboardInterrupt`;
every restoration failure is retained and reported without hiding the original
error or the acquired data.

Realized as a participant-based `RestorationTransaction`:

```python
with RestorationTransaction(client) as tx:
    tx.preserve("tip", TipState.snapshot(client))
    original = tx.preserve("bias_spectroscopy", BiasSpectroscopySettings.snapshot(client))
    ...                                   # configure, acquire
    tx.attach_result(result)              # retained even if later cleanup fails
# on exit: if recovery allows, restore participants in reverse order, best-effort,
# aggregating every failure into one StateRestorationError(original_error, failures, result)
```

> Typed participants (`TipState`, `BiasSpectroscopySettings`) keep their own
> snapshot/restore logic; the transaction only coordinates ordering, recovery
> gating, failure aggregation, and result retention. See the plan §2.

### Typed configuration objects

Replace nested DataFrames/pickles with dataclasses (or Pydantic) such as
`BiasSpectroscopyConfig`, `ScanConfig`, `TunnelParameters`, `RFSweepConfig`,
`PulseSequenceConfig`. Each carries explicit units and validation. Validation is
I/O-free and runs before any command is sent; optional fields use `None` = "leave
as-is" so defaults never overwrite valid settings with unsafe zeros.

Provide an explicit `to_metadata()` (serializable provenance) rather than
promising generic JSON serialization: configs may hold runtime callbacks and
hardware interfaces (e.g. `external_bias_restorer`) that are **not** serializable.
Keep those injected separately and excluded from the serialized form.

### Experiment provenance

Store in every QCoDeS dataset: command-configuration revision, software Git
commit, Nanonis version, station snapshot, workflow configuration, and
acquisition timestamps/duration. (With acquire-first persistence the dataset's
own timestamp is the *persist* time, not the measurement time — capture both.)

### Two-tier testing (no simulator)

A Nanonis software simulator is **not** a validation gate. Two tiers instead:

1. **Logic doubles (fast, CI):** `FakeController` in-process test doubles with no
   socket / QCoDeS / DB — they pin orchestration logic (restoration order,
   recovery gating, config validation, normalization) and guard regressions.
2. **Live-hardware validation (authoritative):** every workflow is validated
   against **real Nanonis hardware over a real socket**. Response shapes,
   magic-int meanings, timing, and file behaviour are only trusted from the real
   controller — this is the acceptance gate, not a simulator.

Because the live path sends state-changing commands to a real STM, **mandatory
preflight + guarded/neutral-argument handling is a hard requirement of the
live-test harness**, not a nicety.

## Adoption backlog (by status)

### Realized (bias spectroscopy + scan + data-readers verticals)

Status: **three verticals implemented; full suite at 204 tests passing;
live-hardware validation done for spectroscopy and partially done for scan.**
Live-hardware validation over a real socket is the acceptance gate for the
hardware verticals; the read-only data vertical is gated on real-file oracle
comparison instead. A simulator is not used.

Two end-to-end hardware workflows are built to the full standard — typed config,
Nanonis state snapshot, recovery-gated best-effort restoration, lossless
normalization, and (for spectroscopy) acquire-first QCoDeS registration with
provenance metadata. A third, read-only vertical (`data/`) reads Nanonis files
into immutable typed models — the reduced form of the canonical shape.

**Bias spectroscopy** — live-validated:

- **Spectroscopy configuration round trips** — read, save, modify, and restore
  complete spectroscopy settings via typed snapshots and command groups
  (`BiasSpectroscopySettings` snapshot-and-patch).
- **State transactions, typed configs, provenance** — the cross-cutting
  requirements above, in their first concrete form.

**Full scan (M4)** — implemented; live-validation in progress (see
[`scan_workflow_walkthrough.md`](scan_workflow_walkthrough.md)):

- **`ScanWorkflow.run()`** — corner positioning, frame/buffer/speed/props
  snapshot-and-patch, continuous-scan forced off, PDF-defined direction,
  separate controller/socket timeouts, per-channel × per-direction `FrameDataGrab`,
  stop-and-confirm recovery, and an immutable self-describing `ScanResult`.
- **`ScanWorkflow.run_partial()`** — acquires the first N image rows (counted by
  trace returns off `Scan.WaitEndOfLine`) then stops; a preview / drift-check /
  early-abort path. `Scan.WaitEndOfLine` semantics were characterized live
  (2026-07-01): ~2 returns per image row, 1-based `line_number`, variable-length
  startup transient.
- **Shared toolkit generalizations landed** — generic `recover_module` (vertical-
  neutral `RecoveryReport.module_stopped`) and shared `TipRestorePolicy`
  (in `workflows/models.py`; a dedicated `policies.py` is still not needed).
- **QCoDeS scan persistence (M4-D) is now implemented** (`qcodes/scan.py`,
  built 2026-07-01 once the row-orientation gate below was closed): 2-D index
  meshgrid setpoints + optional physical `x_m`/`y_m` grids from the confirmed
  `row_order`, per-channel×direction images, and provenance metadata — the same
  acquire-first pattern as the spectroscopy adapter.

> **`FrameDataGrab` row orientation — characterized live (2026-07-01).** A
> sample-independent partial-scan test (`examples/verify_row_orientation.py`,
> `run_partial` up + down on a 16-line frame at angle 0) settled it on the
> `127.0.0.1:6501` rig: *up* filled matrix rows 10–15 and *down* filled rows 0–5 —
> **opposite** ends, so the buffer is **physically-indexed** (up/down do **not**
> reverse row order; `row_order` is a single constant), and matrix row 0 is the
> frame's top edge → **`row_order = "top_to_bottom"`**. The Nanonis GUI confirms
> the convention this rests on in **both** directions — *up* rasters bottom→top and
> *down* rasters top→bottom (scanned rows build from the start edge inward) — so the
> result is fully confirmed, not conditional.
> `scan/geometry.py` can now be given this `row_order`. Still uncharacterized:
> `column_order` (fast-axis left/right) and the real `PropsGet` autopaste encoding.
> `ScanResult` still preserves raw matrix order and the explicit controller scan
> direction.

> **Known limitation — backward sweeps don't map cleanly onto QCoDeS setpoints.**
> The persistence adapter (`qcodes/spectroscopy.py`) only registers
> `configured_voltage` as a setpoint for **forward-only** sweeps where
> `data_columns == points`. When `effective.include_backward` is set, the bias
> axis is non-monotonic (forward then reverse over the same voltages), which the
> QCoDeS setpoint model cannot express as a single coordinate; the adapter falls
> back to registering only `sample_index` and logs a warning. This is a genuine
> friction of the QCoDeS data model, not a bug — the domain `BiasSpectroscopyResult`
> still carries both directions losslessly (`forward_axis()` / `backward_axis()`).
> If bidirectional persistence is ever needed, the fix is to characterize the
> direction split and register forward/backward as separate traces (or add a
> `direction` coordinate), not to flatten the data. Tracks the broader point that
> QCoDeS persistence is optional/dormant at the current stage.

**Data readers (`data/`)** — implemented; oracle-validated against real files (see
[`data_readers_walkthrough.md`](data_readers_walkthrough.md)):

- **`read_sxm` / `read_3ds` / `read_dat` / `read_session`** return immutable, typed
  domain models (`SxmData`, `Grid3DData`, `DatData`, `SessionConfig`) with SI
  conversion, structural validation, `NaNPolicy` handling, and `to_metadata()`
  provenance (parser + package version + git commit + controller Nanonis version).
- **Hardware-free leaf** — imports only `nanonis.geometry`/`types` + numpy +
  nanonispy; controls no hardware. `spaik`'s `SXM`/`Nanonis3ds` recipes were
  adopted (orientation convention, `DATA_INFO` handling) but not its structure
  (god-class, `assert`s, pickle, in-place file writes).
- **Orientation lives in adapters, never in readers** — readers preserve raw
  matrix order + `:SCAN_DIR:`; `data/adapters/xarray.py` and `qcodes/data.py` apply
  the confirmed SXM file convention (up→flip rows, backward→flip cols) with physical
  grids. 3DS orientation has no oracle yet, so `grid_3ds_to_xarray` requires a
  caller-declared `row_order` and flags it unverified.
- **Independent transforms** — `data/transforms.py` rebuilds `spaik`'s
  background-correction catalogue as pure, NaN-safe functions; no reader applies
  them (raw data stays raw; correction is an explicit downstream step).

> **Known follow-ups (from the walkthrough review).** The SXM header-only
> **fallback decode path is untested** (the only `.sxm` fixture is uniformly
> `both`; a single-direction fixture would exercise it — and note truncated-file
> rejection currently *depends* on that fallback's size check). Only **one `.dat`
> variant** is fixture-covered. Neither blocks the vertical; both are tracked, not
> hidden.

### Foundation backlog (shared toolkit, not a vertical)

- **Multi-instrument interfaces** — `RFSource`, `AWG`, `LockIn`, `BiasSource` as
  `Protocol`s / abstract interfaces. `spaik` shows why they are needed; its
  concrete runtime type-switching must **not** be copied. Today only
  `CommandClient` / `RecoverableCommandClient` exist — these are still
  architectural intent, built when a vertical (e.g. RF sweeps) needs them.
- **Shared restoration policies** — `policies.py` (`TipRestorePolicy`, bias
  ramping) extracted from `BiasSpectroscopySafetyPolicy` once scan/tunnel reuse
  tip restoration. Rig-specific numeric limits and workflow-specific preflight
  rules stay **injected**, not centralized.
- **Cooperative cancellation + progress events — promoted to an M5a
  prerequisite** (`workflows/cancellation.py`: a `CancelToken` checked between
  commands, plus progress callbacks). The drift loop runs for hours and
  atom-tracking maps for ~12 h; `KeyboardInterrupt` is not a cancellation
  mechanism. Built *before* the datalog vertical, which is its first consumer.
- **Second-connection concurrency (M6, not before).** Background drift
  compensation cannot share the measurement connection — the command socket
  blocks for an entire acquisition (`BiasSpectr.Start`), so a lock does not
  help. The design: a plain daemon `threading.Thread` owning a **dedicated
  `CommandClient` on a second Nanonis port** (the controller serves 6501–6504
  simultaneously), a **single-writer rule** (while running, the compensator is
  the only writer to `Piezo.DriftComp*`), exposed as a context manager
  (`with compensator.running(): spectroscopy.run(...)`). One thread updating
  one module every few seconds is the entire concurrency requirement —
  **no asyncio migration** of the protocol/command layers.
- **Rig/session configuration — replaces `spaik`'s `session.pkl`, which is not
  adopted.** Split what it conflates: (1) rig/session config → a frozen
  `RigConfig` dataclass parsed from a per-rig TOML file (ports, data folders,
  policy limits) — human-readable, git-diffable, refactor-safe, no code
  execution on load; (2) parameter presets → named JSON files round-tripped
  through typed configs (`to_metadata()`-style), never a mutable `_latest`
  file that makes runs depend on whoever measured last; (3) measurement data →
  Nanonis files + domain results remain the source of truth, QCoDeS DB stays an
  optional adapter, never load-bearing. Adopt one idea from `spaik`'s session
  handling: a small `SessionPaths` helper wrapping `Util.SessionPathSet` for
  dated session folders. No pickle anywhere.
- **Reusable acquisition utilities** — reproducible randomized ordering (shuffled
  sweep/pulse order with a stored seed) as a shared utility consumed by verticals,
  **not** a workflow of its own.

### Vertical backlog (proven recipes still to rebuild)

The full scan workflow and the Nanonis data readers are **realized** (see the
Realized section). In priority order:

1. **Time-trace datalog (M5a)** — `workflows/datalog/` as specified under
   Subsystem responsibilities: polling backend first, typed `TimeTraceConfig` /
   immutable `TimeTraceResult`, RT/tip state untouched on exit. Prerequisites:
   `workflows/cancellation.py` (Foundation, promoted) and `Signals.ValsGet` in
   `configs/commands`. It is deliberately small — its purpose is to feed the
   drift vertical.
2. **Drift compensation (M5b + M6)** — `workflows/drift/` as specified under
   Subsystem responsibilities. M5b is the pure `LogDriftModel` plus a
   **synchronous** `DriftCompensationWorkflow` (the notebook use case:
   compensate, converge, then measure). M6 adds the background
   `DriftCompensator` on a second-port client (Foundation entry above), so
   compensation keeps updating *during* spectroscopy or scans. Requires **no**
   lab-policy decisions — no tunnel ramping, no zero crossing — which is why it
   jumps the queue.
3. **Z spectroscopy (M7)** — near-transcription of the bias-spectroscopy
   vertical (same snapshot-and-patch, transaction, result shape); needs a
   `ZSpectr.json` command group (absent today — `spaik`'s complete ZSpectr
   coverage is the reference for the command surface, including the retract
   safety settings).
4. **Generic sweeper (M7)** — typed `GenericSweepConfig` over the GenSwp module
   (`GenSwp.json` absent today). `spaik`'s `gen_sweep` / `doTipFieldSweep`
   show how much lab mileage this module carries; the multi-instrument
   `Protocol` interfaces (Foundation) stay dormant until this vertical proves
   they are needed.
5. **Atom tracking and hyperscanning** — `atom_tracking(duration, settings)` as a
   safe context manager; grid/spiral coordinate generation; scan-each-tile;
   optional Z-range/contact verification. Needs an `AtomTrack.json` command
   group (absent today). **Requires checkpoint/resume semantics**
   (incremental map persistence so a 12-hour run resumes after failure) as a
   prerequisite, not an afterthought. It builds directly on the realized pieces:
   many `ScanRegion`s over one `ScanConfig`, with `data/` readers closing the loop
   on the saved tiles.

Small adoptable primitive, not a vertical: `spaik`'s **Δz cross-pattern
measurement** (`meas_dz` — Z at a point and four surrounding points,
before/after a manipulation, robust against tip changes) as a pure helper
returning a typed result. Its callers (pickup/poke pulses) stay blocked below.

### Blocked by lab policy

Real work, but cannot start until the lab settles the safety questions — kept
separate so they do not contend with the priority order above.

- **Tunnel-parameter ramping** — reimplement `setTunnelParameters` with explicit
  current/bias ramp rates, a zero-crossing policy, cancellation and timeout,
  feedback-state checks, real exceptions instead of assertions, and simulator
  tests. *Blocked:* zero-crossing permitted? feedback off during ramp?
  interrupted-halfway behaviour? (See plan §2/§8.) Shares mechanics with the
  scan vertical's tip restoration.
- **Transfer-function-aware RF sweeps** — request a voltage at the STM junction
  and compute generator/AWG output from the measured frequency-dependent transfer
  function. *Blocked:* requires the measured transfer function and the
  `RFSource` / `AWG` interfaces (Foundation backlog).
- **Tip-conditioning pulses** — `spaik`'s `pickUp` / `pokeTip` / `atom_pickup`
  recipes (feedback off, blind Z excursion, bias pulse, restore). The Δz
  verification primitive is adopted separately (Vertical backlog); the pulse
  procedures themselves need the same zero-crossing / feedback-off /
  interrupted-halfway policy decisions as tunnel ramping. *Blocked:* same
  questions as tunnel-parameter ramping.
- **Z-range auto-recovery** — `spaik`'s `checkZrange` recipe (withdraw → coarse
  motor +Z → adjust motor amplitude → soft-setpoint auto-approach → restore)
  is genuinely valuable for unattended long runs, but it drives the coarse
  motor with hard-coded gains and fixed 30/90 s sleeps instead of confirmed
  completion. *Blocked:* a rig-approved motor/approach policy; when built,
  completion must be confirmed by status polling, never fixed sleeps.

## Next milestone

Two tracks. The open scan-gate items carry over and close alongside M5 — they
do not block it (see [`scan_gate_plan.md`](scan_gate_plan.md)): rig safety-limit
approval (`examples/rig_safety_policies.py` reviewed, `approved=True`, dated),
fast-axis `column_order` characterization, and the paired autosaved `.sxm` +
`ScanResult` run that validates the reader's orientation (scan gate G-3).

The new-vertical track, in order:

1. **M5a — cancellation + time-trace datalog.** Build
   `workflows/cancellation.py` (`CancelToken` + progress events), add
   `Signals.ValsGet` to `configs/commands`, then the polling
   `TimeTraceWorkflow`. Live acceptance: a 60 s Z(t) trace with feedback on,
   sample timing verified against the wall clock, tip state and any touched
   settings untouched on exit.
2. **M5b — drift model + synchronous compensation.** `LogDriftModel` as pure,
   CI-tested fitting (synthetic log data + noise, sign flips, near-zero drift,
   fit divergence), then `DriftCompensationWorkflow.run(trace, config)`. Live
   acceptance is self-verifying: record trace → fit → compensate → record a
   second trace → **the residual drift rate must drop by an order of
   magnitude**. Must be characterized live before trusting: `Piezo.DriftCompSet`
   **units, sign convention, and saturation-limit semantics** (`spaik` applies
   the fitted rate with no sign handling — do not trust it). `FakeController`
   tests pin: rate-above-clamp, transport loss mid-loop (recovery gates the
   exit write), `KeyboardInterrupt` between updates, a second interrupt during
   restoration, trace shorter than the fit window.
3. **M6 — background compensation.** The `DriftCompensator` context manager on
   a dedicated second-port client with the single-writer rule (Foundation
   entry), so compensation keeps updating while spectroscopy or scans run on
   the main connection.
4. **M7 — Z spectroscopy, then the generic sweeper** (Vertical backlog items
   3–4), each needing its command group (`ZSpectr.json`, `GenSwp.json`)
   live-validated first.

As always, no vertical starts before its state model, safety policy,
timeout/recovery contract, result model, and **live-hardware acceptance
criteria** are specified — the canonical vertical shape above. Starting without
them would repeat the unsafe assumptions this rebuild exists to remove.

## References

- [`workflow_layer_plan.md`](workflow_layer_plan.md) — review-hardened design for
  the bias spectroscopy vertical (rev. 7, milestones M0–M4).
- [`workflow_layer_walkthrough.md`](workflow_layer_walkthrough.md) — what has been
  implemented and validated.
- [`scan_workflow_plan.md`](scan_workflow_plan.md) — the scan vertical (M4), with
  the two toolkit generalizations a second vertical forces.
- [`scan_gate_plan.md`](scan_gate_plan.md) — closing the scan live-hardware gate
  (rig approval, `column_order`, full autosaved run — which feeds the reader oracle).
- [`data_readers_plan.md`](data_readers_plan.md) — design of the realized `data/`
  vertical (neutral primitives, readers, transforms, adapters).
- [`data_readers_walkthrough.md`](data_readers_walkthrough.md) — what was built,
  verified, and the known follow-ups.
- [`datalog_plan.md`](datalog_plan.md) — implementation plan for M5a: the
  cancellation toolkit and the general-purpose time-trace datalog vertical.
- [`datalog_liveview_plan.md`](datalog_liveview_plan.md) — proposal: per-sample
  event hook + example-layer live plotting for running time traces.
- [`datalog_walkthrough.md`](datalog_walkthrough.md) — what was implemented,
  verified offline, and what remains for live characterization and acceptance.
- [`drift_plan.md`](drift_plan.md) — implementation plan for M5b: drift model +
  synchronous compensation (consumes datalog's `TimeTraceResult`), with the
  `DriftCompSet` live characterization and acceptance gates.
- [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) — the file-reader
  dependency for `data/` (project pins released `nanonispy==1.1.0`; see walkthrough).
