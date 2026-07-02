# Blueprint — What to Adopt from `spaik`

Status: strategic blueprint · Date: 2026-07-01 (scan + data-readers verticals
moved to Realized; shared `geometry`/`types` primitives extracted)

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
    spectroscopy/            #   bias spectroscopy (implemented + live-validated)
    scan/                    #   full scan workflow (implemented; run + run_partial)
      models.py              #     ScanRegion now composes geometry.FrameGeometry
      geometry.py            #     compat re-export of nanonis.geometry
    tunnel/                  #   prepare/restore tunnelling conditions
    datalog/
    atom_tracking/

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
- **Reusable acquisition utilities** — reproducible randomized ordering (shuffled
  sweep/pulse order with a stored seed) as a shared utility consumed by verticals,
  **not** a workflow of its own. Likewise progress events and cooperative
  cancellation (a cancel token + callbacks) for long-running workflows.

### Vertical backlog (proven recipes still to rebuild)

The first two items — the full scan workflow and the Nanonis data readers — are
now **realized** (see the Realized section). The next unbuilt vertical is:

- **Atom tracking and hyperscanning** — `atom_tracking(duration, settings)` as a
  safe context manager; grid/spiral coordinate generation; scan-each-tile;
  optional Z-range/contact verification. **Requires checkpoint/resume semantics**
  (incremental map persistence so a 12-hour run resumes after failure) as a
  prerequisite, not an afterthought. It builds directly on the realized pieces:
  many `ScanRegion`s over one `ScanConfig`, with `data/` readers closing the loop
  on the saved tiles.

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

## Next milestone

The scan vertical is built; the milestone now is **closing its live-hardware
acceptance gate**, not writing a new vertical. Concretely, in order:

1. **Approve rig safety limits.** Get `examples/rig_safety_policies.py` reviewed and
   `approved=True` (dated, version bumped). No scan runs against unapproved
   3 µm / 1.5 µm piezo limits.
2. **Characterize `FrameDataGrab` row orientation live** — **DONE (2026-07-01).**
   The sample-independent partial-scan method (`examples/verify_row_orientation.py`,
   up + down) found a physically-indexed buffer with `row_order = "top_to_bottom"`
   (see the Realized callout). Remaining orientation bits (`column_order`, autopaste
   encoding) are minor and can be settled alongside the adapter work.
3. **DONE (2026-07-01).** `row_order = "top_to_bottom"` is wired through the M4-D
   QCoDeS scan adapter (`qcodes/scan.py`), which calls `scan_coordinate_grids` for
   the physical grids. Remaining: characterize fast-axis `column_order` (physical X
   may be mirrored until then; index grids are unaffected).

The **data-readers vertical was built in parallel** (it is hardware-free, so it
neither contends with the scan gate nor needs the rig) and is realized. It leaves
one live tie-in for the scan gate: the paired autosaved `.sxm` + `ScanResult` that
validates the reader's orientation (scan gate G-3), still pending. The next
**hardware** vertical (atom tracking) begins only after its state model, safety
policy, timeout/recovery contract, result model, and **live-hardware acceptance
criteria** are specified — the same discipline, following the canonical vertical
shape above. Starting without them would repeat the unsafe assumptions this rebuild
exists to remove.

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
- [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) — the file-reader
  dependency for `data/` (project pins released `nanonispy==1.1.0`; see walkthrough).
