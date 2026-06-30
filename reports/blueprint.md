# Blueprint — What to Adopt from `spaik`

Status: strategic blueprint · Date: 2026-06-30

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
            protocol/                 # TCP transport + exceptions + TransportState
               ▲
            command/                  # registry, encoder/decoder, controller
               ├──────────────┐
               ▼              ▼
          workflows/      qcodes/ instrument + channels
               │ returns       ▲ consume results
               ▼               │
          domain results ──────┘ → qcodes/ persistence adapters → QCoDeS datasets

          data/ readers → domain data → optional QCoDeS / xarray adapters
```

```text
nanonis/
  protocol/                  # exists
  command/                   # exists

  workflows/                 # transactional measurement recipes (in progress)
    protocols.py             #   CommandClient, RecoverableCommandClient
    errors.py                #   WorkflowError hierarchy
    state.py                 #   RestorationTransaction, TipState, recover_module
    policies.py              #   shared TipRestorePolicy / bias ramping (emerges with scan)
    spectroscopy/            #   bias spectroscopy (implemented) + others
    scan/                    #   full scan workflow (next vertical)
    tunnel/                  #   prepare/restore tunnelling conditions
    datalog/
    atom_tracking/

  qcodes/                    # optional adapter (exists)
    instrument.py
    spectroscopy.py          #   persistence adapter: result -> QCoDeS dataset
    scan.py

  data/                      # STM data models + readers (future)
    readers/                 #   sxm.py, three_ds.py, dat.py
    adapters/                #   xarray.py  (a data->QCoDeS adapter lives in qcodes/)
```

**Dependency direction (non-negotiable):** `workflows -> command API + the
protocol layer's stable error/state types` (`NanonisTimeoutError`,
`NanonisConnectionError`, `NanonisProtocolError`, `TransportState`). Those are the
protocol layer's public contract, so depending on them is allowed and is stated
here explicitly. The workflow package imports nothing from `nanonis.qcodes` and
nothing from `qcodes`. Units are volts / SI, matching `configs/commands`. No
pandas, no pickle in this layer.

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
- **`data/`** — STM data models, Nanonis file readers (`sxm`, `three_ds`, `dat`),
  and transforms with `validation`. It must **not** control hardware. Readers
  produce **domain data**; optional adapters turn that into QCoDeS datasets or
  xarray objects (a data→QCoDeS adapter lives under `qcodes/`). Reuse
  [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) for the model layer.

> **Design note — no separate `safety/` package.** The original sketch proposed a
> top-level `safety/` (policies, preflight, ramping, errors). The realized design
> instead *injects* a typed, rig-specific `BiasSpectroscopySafetyPolicy` into each
> workflow, with preflight and ramp policy living next to the workflow that uses
> them. This keeps safety rules reviewable and per-rig without creating a second
> quasi-god service. Treat safety as a **cross-cutting concern injected into
> workflows**, not a standalone subsystem.

## Cross-cutting requirements

Every workflow must satisfy these, regardless of which recipe it implements.

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

### Realized (bias spectroscopy vertical)

Status: **implemented; logic doubles complete (106 `FakeController` tests);
live-hardware validation pending** (no controller was reachable in the build
session — see the walkthrough). Live-hardware validation over a real socket is the
acceptance gate; a simulator is not used.

The first end-to-end workflow is built to the full standard — typed config,
Nanonis state snapshot, recovery-gated best-effort restoration, lossless
normalization, and acquire-first QCoDeS registration with provenance metadata.

- **Spectroscopy configuration round trips** — read, save, modify, and restore
  complete spectroscopy settings via typed snapshots and command groups
  (`BiasSpectroscopySettings` snapshot-and-patch).
- **State transactions, typed configs, provenance** — the cross-cutting
  requirements above, in their first concrete form.

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

In rough priority order:

1. **Full scan workflow** — adopt the `doScan` sequence (corner positioning,
   frame/buffer/speed, start, wait, timeout) and return a `ScanResult`. The next
   vertical; design is in [`scan_workflow_plan.md`](scan_workflow_plan.md).
2. **Nanonis data readers** — `data/readers/{sxm,three_ds,dat}`, kept independent
   of control code, feeding domain data → optional QCoDeS / xarray adapters.
3. **Atom tracking and hyperscanning** — `atom_tracking(duration, settings)` as a
   safe context manager; grid/spiral coordinate generation; scan-each-tile;
   optional Z-range/contact verification. **Requires checkpoint/resume semantics**
   (incremental map persistence so a 12-hour run resumes after failure) as a
   prerequisite, not an afterthought.

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

One additional end-to-end workflow — **prefer scan** — built to the same contract
as bias spectroscopy:

- typed configuration with I/O-free validation,
- Nanonis state snapshot of the state it mutates,
- a domain `ScanResult` return (a separate `qcodes/` adapter persists it),
- recovery-gated best-effort restoration on every exit path,
- `FakeController` logic doubles, **and live-hardware validation over a real
  socket** as the acceptance gate,
- provenance metadata.

Do not start a second vertical before its state model, safety policy,
timeout/recovery contract, result model, and **live-hardware acceptance criteria**
are specified — starting without them would repeat the unsafe assumptions this
rebuild exists to remove.

## References

- [`workflow_layer_plan.md`](workflow_layer_plan.md) — review-hardened design for
  the bias spectroscopy vertical (rev. 7, milestones M0–M4).
- [`workflow_layer_walkthrough.md`](workflow_layer_walkthrough.md) — what has been
  implemented and validated.
- [`scan_workflow_plan.md`](scan_workflow_plan.md) — the next vertical (M4): scan
  workflow, with the two toolkit generalizations a second vertical forces.
- [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) — proposed data-model
  / file-reader dependency for `data/`.
