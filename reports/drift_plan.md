# Drift Compensation Vertical — Implementation Plan (M5b)

Status: implementation plan, rev. 2 (split from the combined M5 plan) ·
Date: 2026-07-02
Scope: **M5b** — the drift model and the synchronous
`DriftCompensationWorkflow`. **M6** (background compensation on a second-port
client) is previewed but explicitly out of scope.

Prerequisite: the datalog vertical ([`datalog_plan.md`](datalog_plan.md),
M5a) must be complete — this vertical *consumes* a `TimeTraceResult`; it never
acquires data itself. That boundary is deliberate: datalog is a
general-purpose feature, and everything drift-specific (fitting, rate
policy, `Piezo.DriftComp*` writes) lives here and only here.

Parent vision: [`blueprint.md`](blueprint.md) (Subsystem responsibilities →
`workflows/drift/`; Next milestone). Template: the canonical vertical shape —
*typed config → injected policy → transactional run → immutable result* — as
realized in [`workflow_layer_plan.md`](workflow_layer_plan.md) and
[`scan_workflow_plan.md`](scan_workflow_plan.md).

## Context

Drift compensation is the flagship GUI-impossible recipe adopted from `spaik`:
the Nanonis GUI applies a *constant* drift velocity, while
`spaik.driftCompensation` feeds forward the *decaying* rate of a fitted
logarithmic creep model — the physically correct model for post-approach
creep. The recipe is right; the implementation is the defect catalogue this
rebuild exists to avoid:

- an inverted condition (`if drift <= 10e-12: apply; else: break`) whose
  printed message contradicts its behaviour — a bad fit silently stops
  compensating;
- the time base parsed from a *filename* (`TimeTrace_%Y%m%d_%H%M%S_Z`) and
  advanced with wall-clock `datetime.now()`;
- a `finally:` that writes `vx=0, vy=0`, destroying any configured lateral
  compensation, and always leaves the module on regardless of prior state;
- a 10 Hz write loop for a quantity that changes by percent per minute;
- `KeyboardInterrupt` as the only cancellation mechanism.

Everything needed is already available: `Piezo.DriftCompSet/Get` are in
`configs/commands`, and M5a supplies the trace. **No lab-policy blockers** (no
tunnel ramping, no zero crossing, no motor moves) — which is why this vertical
jumps the queue.

## Design rules (inherited + vertical-specific)

Inherited unchanged: SI units; typed frozen configs with I/O-free validation;
injected rig-approved policy; `RestorationTransaction` with recovery-gated
restoration; immutable results with `to_metadata()` provenance; no
pandas/pickle; `FakeController` doubles + live acceptance.

Vertical-specific:

- **The controller owns the velocity; Python owns the schedule.**
  `Piezo.DriftCompSet` is applied in hardware continuously — the loop only
  *updates* the value. The log model's rate changes by a few percent per
  minute after the first minutes, so the update cadence is 1–10 s.
- **Never write an axis you did not decide.** `Piezo.DriftCompSet` takes
  Vx/Vy/Vz together (wire keys `vx_m_s`, `vy_m_s`, `vz_m_s`,
  `saturation_limit`). Every write re-uses the snapshotted Vx/Vy and changes
  only Vz (until a lateral model exists).
- **Explicit exit reasons.** The loop terminates only through a
  `DriftExitReason` enum; no bare `break`. This makes `spaik`'s inverted
  condition unwritable.
- **Fitting is pure and separate.** `fitting.py` touches no hardware and no
  clock; it is CI-gated on synthetic data before the workflow exists.
- **The exit write is policy, not an accident.** The same explicit
  `DriftExitState` is applied on *every* path — normal completion, cancel,
  error (recovery-gated) — never whichever writes a `finally` happens to reach.

## M5b-0 — Drift model (`workflows/drift/fitting.py`) — pure, CI-gated

```python
class DriftModel(Protocol):
    def rate(self, t_s: float) -> float: ...        # m/s at model time t
    def to_metadata(self) -> dict: ...

@dataclass(frozen=True)
class LogDriftFit:                                   # z(t) = a*ln(t) + b
    a: float; b: float
    t_anchor: datetime      # wall-clock origin of the model's t axis (= trace started_at)
    rms_residual_m: float
    def rate(self, t_s: float) -> float:            # a / t; t_s must be > t_floor
    ...

def fit_log_drift(trace: TimeTraceResult, *, signal: int | str,
                  t_offset_s: float = 0.0) -> LogDriftFit:
```

Linear least squares on the `ln(t)` basis (`np.linalg.lstsq` — **no scipy
dependency**). `t_offset_s` shifts the time origin (creep started at approach,
not at trace start; `spaik` ignores this — default 0.0 matches its behaviour,
a 3-parameter `ln(t + c)` fit is a possible later refinement, not M5b).
Guard rails: reject `t <= 0` samples after offset; raise a typed
`DriftFitError(WorkflowError)` when the trace is shorter than a minimum span
(default: require max(t)/min(t) ≥ 5, i.e. enough decades to constrain `a`) or
when the residual exceeds a caller-supplied bound.

The `DriftModel` protocol keeps the workflow model-agnostic: a linear model, a
double-log model, or a lab-supplied callable can replace `LogDriftFit` without
touching the loop.

CI tests (`tests/workflows/drift/test_fitting.py`) on synthetic data: exact
recovery on noiseless log data; tolerance under Gaussian noise; both drift
signs; near-zero drift (`a ≈ 0` → rate ≈ 0, no blow-up); constant z; too-short
trace → `DriftFitError`; `rate()` decreasing in t; anchor propagation.

## M5b-1 — Models + state participant (`workflows/drift/models.py`)

```python
class DriftExitReason(Enum):
    CONVERGED = "converged"              # |rate| below policy threshold
    MAX_DURATION = "max_duration"
    CANCELLED = "cancelled"
    RATE_LIMIT_EXCEEDED = "rate_limit"   # model asked for > max rate; see policy
    SATURATED = "saturated"              # controller reports Z axis saturated

class DriftExitState(Enum):
    ZERO_AND_ON = "zero_and_on"          # spaik's behaviour: Vz=0, module on
    RESTORE_PRIOR = "restore_prior"      # put back the DriftCompGet snapshot

@dataclass(frozen=True)
class DriftCompensationPolicy:           # rig-approved, injected (rig_safety_policies.py pattern)
    max_abs_rate_m_s: float              # hard clamp on |Vz| ever written
    convergence_rate_m_s: float          # e.g. 1e-13 (0.1 pm/s) — lab decides
    on_rate_limit: Literal["clamp", "stop"] = "clamp"   # clamp+warn (default) or exit
    exit_state: DriftExitState = DriftExitState.ZERO_AND_ON
    saturation_limit_pct: float | None = None   # None = leave the rig's value untouched

@dataclass(frozen=True)
class DriftCompensationConfig:
    max_duration_s: float
    update_interval_s: float = 2.0
    signal: int | str = "Z (m)"          # which trace signal was fitted (metadata)
    # __post_init__: finite, > 0; update_interval_s <= max_duration_s

@dataclass(frozen=True)
class PiezoDriftState:                   # transaction participant
    status: bool; vx: float; vy: float; vz: float
    saturation_limit_pct: float
    @classmethod
    def snapshot(cls, client) -> "PiezoDriftState":   # Piezo.DriftCompGet
    def restore(self, client) -> dict[str, BaseException]:  # full Set from snapshot
```

The workflow's every `Piezo.DriftCompSet` write sends
`(status=1, vx=snapshot.vx, vy=snapshot.vy, vz=<new>, sat_limit=<policy or snapshot>)`
— lateral compensation preserved verbatim (design rule above).

## M5b-2 — `DriftCompensationWorkflow` (`workflows/drift/workflow.py`)

```python
class DriftCompensationWorkflow:
    def __init__(self, client: RecoverableCommandClient, *,
                 policy: DriftCompensationPolicy) -> None: ...
    def run(self, model: DriftModel, config: DriftCompensationConfig, *,
            cancel: CancelToken | None = None,
            on_progress: ProgressCallback | None = None) -> DriftCompensationResult: ...
```

Structure — the standard transactional shape, with the loop inside:

1. Preflight: policy sanity vs config; `Piezo.DriftCompGet` reachable; model
   anchor is in the past.
2. `RestorationTransaction`: `tx.preserve("piezo_drift", PiezoDriftState.snapshot(...))`
   with a restorer that applies `policy.exit_state` (ZERO_AND_ON writes
   status=1, vz=0, preserved vx/vy; RESTORE_PRIOR replays the snapshot). The
   *same* exit write happens on normal completion — exit state is policy.
3. Loop, every `update_interval_s` via `cancel.wait()`:
   - `t = <monotonic offset> + (loop_start_utc - model.t_anchor).total_seconds()`
     — wall clock read **once** at loop start, then advanced monotonically;
   - `rate = model.rate(t)`; if `|rate| >= policy.max_abs_rate_m_s`:
     clamp + `logger.warning` (or exit `RATE_LIMIT_EXCEEDED` if
     `on_rate_limit == "stop"`) — **never a silent break**;
   - write `Piezo.DriftCompSet` (axis-preserving, above); read back
     `DriftCompGet` every N ticks (N·interval ≈ 30 s): `z_saturated_status`
     → exit `SATURATED`;
   - `|rate| < policy.convergence_rate_m_s` → exit `CONVERGED`;
   - token cancelled → exit `CANCELLED` (mapped, not raised — a cancelled
     compensation is a *successful* early stop; the exit write still runs);
   - elapsed ≥ `max_duration_s` → exit `MAX_DURATION`.
4. On transport error/`KeyboardInterrupt`: `recover_module` with
   `stop=<no-op>` / `status_stopped=lambda c: True` — there is no module
   acquisition to stop; recovery here only means *transport confirmed ready*
   before the exit write is attempted (recovery gating as usual).
5. `DriftCompensationResult` (immutable): `exit_reason`, `applied_t_s` /
   `applied_vz_m_s` history arrays, `final_rate_m_s`, snapshot echo, model +
   config metadata, timestamps. `tx.attach_result(...)` before exit so it
   survives restoration failures.

`workflows/drift/__init__.py` + `workflows/__init__.py` export the config,
policy, enums, `fit_log_drift`, `LogDriftFit`, workflow, and result.

**FakeController tests** (`tests/workflows/drift/test_workflow.py`): scripted
`DriftCompGet/Set` verifying — vx/vy preserved verbatim on every write; clamp
path writes exactly `±max_abs_rate` and warns; `stop` variant exits
`RATE_LIMIT_EXCEEDED`; convergence exits after the right tick; cancel →
`CANCELLED` + exit write still sent; ZERO_AND_ON vs RESTORE_PRIOR exit writes;
saturation flag → `SATURATED`; transport error mid-loop → recovery gates the
exit write (recovered → written; not recovered → `StateRestorationError` with
the original error and **no** blind write); `KeyboardInterrupt` between ticks;
second failure during restoration aggregates into `StateRestorationError`.

## M5b-3 — Live characterization: `Piezo.DriftCompSet` semantics

**Gate before any closed-loop use.** `spaik` applies the fitted rate with no
sign handling — do not trust it. Script `examples/characterize_driftcomp.py`,
run attended, tiny magnitudes, snapshot/restore around everything:

1. **Read-only**: `DriftCompGet` → record status/velocities/saturation on the
   rig; confirm mapping keys (`vx_m_s`, …).
2. **Round-trip**: Set a tiny Vz (+50 fm/s), Get it back, restore. Confirms
   units survive the wire (m/s in = m/s out) and status semantics (0/1 wire
   values vs on/off).
3. **Sign convention** (the critical one): feedback ON, stable tip. Record a
   3-min Z trace with compensation off (the M5a workflow — dogfooding). Apply
   Vz = +X (X ≈ measured natural drift magnitude); record again; then −X;
   restore. The slope change tells whether positive Vz moves the *measured* Z
   up or down, i.e. whether the workflow must write `+rate` or `−rate` to
   *cancel* a fitted `rate`. Record the answer as a constant with the
   evidence, like the scan `row_order` callout.
4. **Saturation limit**: what `saturation_limit_pct` means on this rig and
   what Get reports when the limit engages (drive a large-ish Vz for seconds
   only if the operator approves; otherwise document from the manual and mark
   unverified).

Findings go into a dated live report + a `DRIFT_SIGN` constant (or policy
field) with the characterization referenced.

## M5b-4 — Live acceptance (end-to-end)

Script `examples/live_drift_compensation.py`, the notebook's recipe rebuilt:

1. `TimeTraceWorkflow`: 3–5 min Z trace, feedback on, compensation off.
2. `fit_log_drift` → report `a`, `b`, RMS residual, current rate.
3. `DriftCompensationWorkflow.run` for 10–15 min (attended; Ctrl-C must exit
   `CANCELLED` cleanly with the exit write applied).
4. Second Z trace under the *exit-state* compensation.
5. **Gate: the residual linear drift rate in trace 2 is at least ~10× smaller
   than trace 1's fitted rate** (the order-of-magnitude criterion from the
   blueprint), and the applied-Vz history is smooth and monotonic-decaying.

## Module/test layout

```text
src/nanonis/workflows/
  drift/{__init__,models,fitting,result,workflow}.py  # M5b-0/1/2
tests/workflows/
  drift/{test_fitting,test_workflow}.py
examples/
  characterize_driftcomp.py             # M5b-3
  live_drift_compensation.py            # M5b-4
```

Suggested commit slices = the milestone numbers (each lands green: code +
tests + exports + doc touch).

## Open questions (resolve at the marked milestone)

1. Sign convention and saturation semantics of `DriftCompSet` — **M5b-3**.
2. `convergence_rate_m_s` value — lab decision at policy sign-off (`spaik`
   used 1 fm/s, likely below measurement noise; propose 0.1 pm/s and let the
   rig owner set it).
3. Exit-state default — ZERO_AND_ON matches `spaik`/lab habit; confirm with
   the rig owner at the same sign-off.
4. Whether the anchor mismatch (creep origin vs trace start) matters at real
   timescales — inspect M5b-4 residuals before considering the 3-parameter
   `ln(t + c)` fit.

## M6 preview (out of scope, designed for)

Background compensation while other measurements run: a `DriftCompensator`
context manager owning a daemon thread and a **dedicated `CommandClient` on a
second Nanonis port** (the command socket blocks for an entire acquisition, so
sharing is impossible), with a single-writer rule over `Piezo.DriftComp*`.
M5b's deliberate groundwork: `CancelToken` is thread-safe; every write is
axis-preserving; the exit-state write is policy-driven and idempotent. No
asyncio, ever — one thread updating one module every few seconds is the whole
requirement.

## Non-goals (M5b)

- Acquiring traces (datalog vertical owns that; this vertical takes a
  `TimeTraceResult` argument).
- Lateral (Vx/Vy) drift models — axes are preserved, never modeled, in M5b.
- Background operation (M6), tunnel-condition setup (blocked tunnel
  vertical), QCoDeS persistence (dormant by policy).

## References

- [`blueprint.md`](blueprint.md) — vision, backlog, milestone ordering.
- [`datalog_plan.md`](datalog_plan.md) — prerequisite vertical (M5a) that
  produces the `TimeTraceResult` consumed here.
- `spaik/src/spaik/SPMMeasurement.py` — `driftCompensation` (l. 7116): the
  recipe and the defect catalogue.
- `spaik/example/commands_DriftCompensation.ipynb` — the workflow being
  rebuilt.
- `TCPProtocol_SPM.pdf` — §Piezo (DriftCompSet/Get semantics).
- [`scan_workflow_plan.md`](scan_workflow_plan.md) — the transactional-vertical
  template this plan instantiates.
