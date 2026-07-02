# Datalog Vertical — Implementation Plan (M5a)

Status: implementation plan, rev. 5 (third review round: rebase only after a
*counted* overrun — the unconditional `max()` rebase accumulated sleep jitter
into schedule drift; `Util.VersionGet` may map only `NanonisCommandError` to
`None`, transport failures propagate. Rev. 4: lateness measured at acquisition
start, rebase-after-overrun scheduling, NaNPolicy values ALLOW/WARN/RAISE,
strict response-field validation, float-safe sample count, provenance
sourcing, peak-memory statement) · Date: 2026-07-02
Scope: **M5a** — the cancellation/progress toolkit and the polling time-trace
datalog vertical. This vertical is **general-purpose**: drift compensation
([`drift_plan.md`](drift_plan.md)) is its *first* consumer, not its purpose.
Other consumers it must serve without change: noise/stability characterization
before a measurement session, signal-vs-time monitoring during long
experiments, settling-time measurement after parameter changes, and any future
recipe that starts with "record channel X for N seconds".

Parent vision: [`blueprint.md`](blueprint.md) (Subsystem responsibilities →
`workflows/datalog/`; Next milestone). Template: the canonical vertical shape —
here in its **reduced, read-only form** (like `data/`): *typed config →
validate → acquire → immutable result*, no safety policy, no transaction,
because nothing is mutated.

## Context

`spaik.doDataLogging` proves the lab needs scripted time traces, but it
conflates three jobs: establishing tunnel conditions (bias/setpoint/feedback/RT
settings), acquiring the trace (via the file-based Data Logger plus a
`sleep(20)`-and-reread settling hack), and saving pickles. This vertical does
**only the middle job**, by polling — and does it read-only:

- Establishing conditions is the (lab-policy-blocked) tunnel vertical's job.
- Polling the Signals module at 5–20 Hz needs no new socket, no file round
  trip, and no unvalidated command group. It covers every slow-phenomenon use
  case (drift is pm/s; stability monitoring is slower still).
- High-rate backends (TCPLog streaming — schema corrected 2026-07-02 but
  live-unvalidated, data on a separate stream port; the file-based Data Logger
  module — `DataLog.json` transcribed 2026-07-02, likewise live-unvalidated)
  are **deferred**, not designed away: see Extension points.

Working-tree note: `Signals.ValsGet` is already transcribed in
`configs/commands/Signals.json` (uncommitted). M5a-1 verifies it against the
PDF and commits it — the transcription step is partially done, not skipped.

## Design rules (inherited + vertical-specific)

Inherited unchanged: SI units; typed frozen configs with I/O-free
`__post_init__` validation; immutable results with `to_metadata()` provenance;
no pandas/pickle; `FakeController` doubles for CI + live hardware as the
acceptance gate; workflows import nothing from `nanonis.qcodes`.

Vertical-specific:

- **The workflow mutates nothing.** Zero `*.Set` sends — make this an explicit
  review check. No `RestorationTransaction`, no safety policy. If a caller
  wants specific tunnel conditions first, that is the caller's (or a future
  tunnel workflow's) explicit step, visible at the call site.
- **Monotonic time only.** Sample timestamps come from `time.monotonic()`
  relative to a recorded start; wall clock (`datetime.now(timezone.utc)`)
  appears only as provenance (`started_at`/`finished_at`). Never derive a time
  base from a filename.
- **Actual timestamps, not nominal ticks.** The result records when each
  sample was really taken; scheduling lateness is *measured and reported*
  (`late_sample_count`), not hidden by pretending the grid was perfect. The
  loop never skips samples and never fires catch-up bursts: deadlines follow
  the nominal grid while on time and **rebase after an overrun** (see M5a-3),
  so a temporary stall stretches the trace — with the timestamps saying so —
  instead of being papered over by a burst of back-to-back reads.
- **A cancelled trace is a valid result.** Early stop via token returns the
  partial data with `cancelled=True`. What raises: transport failure
  (`NanonisTimeoutError` etc.), malformed responses
  (`TimeTraceResponseError`), and — only under `NaNPolicy.RAISE` — non-finite
  data (`NonFiniteTimeTraceDataError`, which retains the result, matching the
  spectroscopy/scan pattern).
- **All signal reads are float32 — a protocol fact, not a choice.**
  `Signals.ValGet`, `Signals.ValsGet`, and the module-specific getters
  (e.g. `ZCtrl.ZPosGet`) all return wire type `f`. There is no float64 read
  path to fall back to; adequacy is *checked*, not worked around (M5a-1,
  Open question 2).

## M5a-0 — Cancellation + progress toolkit (`workflows/cancellation.py`)

Promoted from the Foundation backlog. First consumer is the datalog loop; the
drift vertical and every future long-running workflow reuse it, and M6's
background thread requires it to be **thread-safe** from day one.

```python
class WorkflowCancelledError(WorkflowError): ...   # add to errors.py

class CancelToken:
    """Thread-safe cooperative cancellation flag (wraps threading.Event)."""
    def cancel(self) -> None: ...
    @property
    def cancelled(self) -> bool: ...
    def raise_if_cancelled(self) -> None:          # raises WorkflowCancelledError
    def wait(self, timeout: float) -> bool:        # interruptible sleep;
        ...                                        # True if cancelled during wait

@dataclass(frozen=True)
class ProgressEvent:
    workflow: str            # e.g. "datalog.time_trace"
    fraction: float | None   # 0..1, or None when open-ended
    message: str
    elapsed_s: float

ProgressCallback = Callable[[ProgressEvent], None]
```

Rules: workflows accept `cancel: CancelToken | None = None` and
`on_progress: ProgressCallback | None = None`; a `None` token means "never
cancelled". `CancelToken.wait()` replaces `time.sleep()` in workflow loops so
cancellation is never delayed by a sleep — and cancellation must additionally
be **checked once per iteration regardless of whether the loop slept** (a loop
running behind schedule skips its sleeps; it must not thereby become
uncancellable). Callback exceptions are caught and logged, never propagated
into the acquisition. In transactional workflows (not this one), cancellation
raises `WorkflowCancelledError` from inside the transaction body so normal
restoration semantics apply; here it just ends the loop (partial result).

**`KeyboardInterrupt` contract:** workflows do *not* catch
`KeyboardInterrupt` — it propagates (in transactional workflows it already
triggers recovery + restoration; in this read-only one there is nothing to
restore). Graceful Ctrl-C is the *caller's* wiring: interactive scripts and
notebooks install a SIGINT handler that calls `token.cancel()` on the first
Ctrl-C (second Ctrl-C restores the default handler and raises). A small helper
`cancel_on_sigint(token)` context manager in `cancellation.py` packages this
so every example does it the same way.

Tests (`tests/workflows/test_cancellation.py`): token starts uncancelled;
cancel → `raise_if_cancelled` raises; `wait` returns early on cross-thread
cancel; callback exception does not propagate; `cancel_on_sigint` cancels on
first simulated SIGINT and restores the previous handler on exit.

## M5a-1 — Verify + commit `Signals.ValsGet`; characterize the Signals group

`Signals.ValsGet` already exists in the working tree (`Signals.json`):
args `signals_indexes_size (i)` / `signals_indexes (1D array int)` /
`wait_for_newest_data (I)`; resp `signals_values_size (i)` /
`signals_values (1D array float32)`. Remaining work, in order:

1. **Verify against `TCPProtocol_SPM.pdf` §Signals** (field order, types,
   whether the index-array size prefix is element count or byte count — the
   same transcription discipline as every other group), then commit.
2. **Response shape is a mapping, not the values — validated strictly.** The
   controller unwraps single-field responses only; `ValsGet` has two response
   fields, so `client.send("Signals.ValsGet", ...)` returns
   `{"signals_values_size": ..., "signals_values": ...}`. The workflow
   **requires** both fields (not "validates when present"): non-mapping
   response, missing key, non-integer `signals_values_size`, size inconsistent
   with the array, or array length ≠ `len(config.signal_indexes)` → each is a
   `TimeTraceResponseError`. `Signals.NamesGet` gets the same strictness when
   resolving names: require `signals_names_number ==
   len(signals_names)`, and every requested signal index must be
   `< signals_names_number` — otherwise `TimeTraceResponseError`. (Pattern:
   the `_mapping(...)` helper in `workflows/models.py`, extended with the
   field checks.)
3. **Dedicated live characterization script** —
   `examples/characterize_signals.py`, *not* an extension of
   `tests/test_live_test_commands.py` (that file is an offline unit test of
   command ordering, not a live suite). Read-only, snapshot-free. It records
   into a dated live report:
   - the rig's `Signals.NamesGet` slot table;
   - `ValsGet` vs `ValGet` vs `ZCtrl.ZPosGet` cross-checks on the Z slot
     (agreement bounds; all three are float32 — see design rules);
   - per-call latency distribution for `ValsGet` (bounds the maximum honest
     polling rate — a documented guideline, not a config hard-code);
   - `wait_for_newest_data` = 0 vs 1 behaviour (the PDF says 1 blocks until
     the next RT publication — measure the added latency and the inter-sample
     regularity both ways; pick the default from data, provisionally 1);
   - float32 quantization step observed on the Z slot vs the pm-scale
     structure the drift fit needs (Open question 2).

## M5a-2 — Models (`workflows/datalog/models.py`, `result.py`)

```python
@dataclass(frozen=True)
class TimeTraceConfig:
    signal_indexes: tuple[int, ...]      # Nanonis signal slots (0..127)
    duration_s: float
    sample_interval_s: float = 0.1       # 10 Hz default
    wait_for_newest_data: bool = True
    resolve_names: bool = True           # Signals.NamesGet once, store slot names

    @property
    def n_samples(self) -> int:          # floor(duration/interval + 1e-9) + 1
        ...                              # (float-safe; see below)

    # __post_init__: non-empty unique indexes in [0, 127]; finite duration_s > 0;
    # finite sample_interval_s > 0; duration_s >= sample_interval_s;
    # n_samples * len(signal_indexes) <= MAX_TRACE_ELEMENTS (10_000_000
    #   elements ~= 80 MB float64 of final storage; peak transient usage is
    #   ~2x that (~160 MB) because the frozen result defensively copies the
    #   workflow's buffers — documented intent, acceptable on lab PCs)
```

**Float-safe sample count:** `duration_s / sample_interval_s` is binary
floating point — `0.3 / 0.1` evaluates to `2.999…96`, so a naive
`floor(ratio) + 1` silently drops the last sample. Policy: ratios within
`1e-9` (absolute, on the ratio) of an integer are treated as that integer —
`n_samples = floor(ratio + 1e-9) + 1`. So `0.3 s / 0.1 s → 4` samples (t = 0,
0.1, 0.2, 0.3) and `60 / 0.1 → 601`, while a genuinely fractional ratio still
floors (`0.35 / 0.1 → 4`, last sample at 0.3). This exact case is
unit-tested.

**Duration semantics (exact):** `duration_s` is the **nominal span** of the
trace. Samples are scheduled at nominal times `k * sample_interval_s` for
`k = 0 .. n_samples-1` with `n_samples` per the float-safe formula above, so
the first sample is at t = 0 and the last is scheduled at the largest multiple
of the interval ≤ `duration_s` (60 s at 0.1 s → 601 samples, last at exactly
60 s; 1 s at 1 s → 2 samples, t = 0 and t = 1 — it *records for one second*).
`duration_s` is **not** a wall-clock deadline: if acquisition runs slow the
trace takes longer (deadlines rebase, M5a-3) and the actual timestamps +
`late_sample_count` report it.

```python
@dataclass(frozen=True)
class TimeTraceResult:                    # arrays np.float64, write=False like SweepAxis
    signal_indexes: tuple[int, ...]
    signal_names: tuple[str, ...]         # () when not resolved
    elapsed_s: FloatArray                 # actual monotonic offsets, NOT nominal ticks
    values: FloatArray                    # shape (n_signals, n_samples)
    requested_interval_s: float
    started_at: datetime                  # UTC — provenance, and the anchor any
    finished_at: datetime                 #   downstream model (e.g. drift fit) uses
    late_sample_count: int                # samples acquired later than the tolerance
    cancelled: bool                       # True when stopped early by token
    nanonis_version: str | None           # Util.VersionGet, read once at run start
    def to_metadata(self) -> dict: ...    # serializes stored fields + config echo +
    def signal_by_index(self, index: int) -> FloatArray: ...   # package/git provenance
    def signal_by_name(self, name: str) -> FloatArray: ...
```

**Provenance sourcing (defined, not promised):** the Nanonis version comes
from a single read-only `Util.VersionGet` at run start, stored on the result.
Error contract: only a controller-reported `NanonisCommandError` ("version
unavailable" — the controller answered, transport intact) yields
`nanonis_version = None`; `NanonisTimeoutError` / `NanonisConnectionError` /
`NanonisProtocolError` **propagate** like anywhere else in the workflow — a
swallowed timeout leaves unread bytes on the socket that would corrupt every
subsequent `ValsGet` frame, so "never abort for a version read" must not
extend to transport failures (which conveniently surface *before* any samples
are acquired). Package version and git commit come from a **neutral top-level
`nanonis/provenance.py`** helper: hoist the existing logic out of
`nanonis/data/_utils.py` (which then delegates to it), following the
`geometry`/`types` precedent — workflows must **not** import from
`nanonis.data` (the sideways dependency the blueprint prohibits).
`to_metadata()` serializes only stored fields plus these helpers' output.

Accessors (names may be duplicated across slots, or unresolved):
`signal_by_index` raises `KeyError` if the slot was not recorded;
`signal_by_name` raises `ValueError` when names were not resolved, when the
name is absent, or when it matches **more than one** recorded slot (the error
message lists the matching indexes and says to use `signal_by_index`). No
polymorphic `signal(index_or_name)` — ambiguity is an error, not a guess.

Invariants (validated in `__post_init__`): `elapsed_s` strictly increasing,
shapes consistent. Non-finite handling is **not** buried here — it is applied
by the workflow through its `nan_policy` (M5a-3), consistent with how
spectroscopy and scan apply `NaNPolicy` (values: **ALLOW / WARN / RAISE**)
from `nanonis.types`. The spectroscopy inspector
(`inspect_non_finite_data`) is typed to `BiasSpectroscopyResult` and is *not*
imported; the datalog vertical gets its own small
`inspect_non_finite_trace(result)` returning a diagnostics dataclass of the
same shape (`nan_count`, `inf_count`, affected signal indexes/names). The
result is deliberately consumer-neutral: it knows nothing about drift,
fitting, or any other downstream use.

New errors in `workflows/errors.py`:

```python
class TimeTraceResponseError(WorkflowError):
    """A Signals response has the wrong shape or an inconsistent length."""

class NonFiniteTimeTraceDataError(WorkflowError):
    """Raised by NaNPolicy.RAISE while retaining the completed result."""
    def __init__(self, result: Any, diagnostics: Any) -> None: ...
```

## M5a-3 — `TimeTraceWorkflow` (`workflows/datalog/workflow.py`)

```python
class TimeTraceWorkflow:
    def __init__(self, client: CommandClient, *,
                 nan_policy: NaNPolicy = NaNPolicy.WARN) -> None: ...
    def run(self, config: TimeTraceConfig, *,
            cancel: CancelToken | None = None,
            on_progress: ProgressCallback | None = None) -> TimeTraceResult: ...
```

Loop skeleton — deadline-scheduled with **rebase-after-overrun**,
cancel-aware. Cancellation is checked **every iteration before sending**,
whether or not the loop slept; sleeping works with or without a token;
lateness is measured **at acquisition start** (after any sleep, so sleep
overshoot is counted); storage is preallocated:

```python
values = np.empty((n_signals, n_samples))          # preallocated, truncated on early stop
elapsed = np.empty(n_samples)
tolerance = 0.5 * config.sample_interval_s          # lateness tolerance (documented)
t0 = time.monotonic(); started_at = datetime.now(timezone.utc)
deadline = t0

for k in range(n_samples):
    if cancel is not None and cancel.cancelled:     # observed even when running late
        break
    remaining = deadline - time.monotonic()
    if remaining > 0:
        if cancel is not None:
            if cancel.wait(remaining):
                break
        else:
            time.sleep(remaining)
    acquisition_started = time.monotonic()          # measured AFTER any sleep —
    lateness = acquisition_started - deadline       #   sleep overshoot counts
    if k > 0 and lateness > tolerance:              # k == 0 explicitly excluded
        late += 1
        deadline = acquisition_started + interval   # rebase ONLY after a counted overrun
    else:
        deadline += interval                        # nominal grid under tolerated jitter
    response = client.send("Signals.ValsGet", len(idx), idx, wait_flag)
    row = _extract_values(response, expected=n_signals)   # strict; TimeTraceResponseError
    elapsed[k] = time.monotonic() - t0
    values[:, k] = row
```

Semantics, stated exactly:

- **Lateness**: sample `k` counts as late when its acquisition *starts* more
  than `tolerance` (= half the interval, a fixed documented fraction — not
  config surface) after its (possibly rebased) deadline, measured *after* any
  sleep so `time.sleep`/`Event.wait` overshoot is counted. `k == 0` is
  explicitly excluded (its deadline is the loop start).
- **Overrun policy — rebase only after a counted overrun, never burst, never
  skip**: while lateness stays within the tolerance, deadlines advance on the
  nominal grid (`deadline += interval`), so ordinary sleep-wakeup jitter does
  **not** accumulate into schedule drift — a naive
  `max(deadline + interval, acquisition_started + interval)` would always
  pick the rebased branch (a sleep never returns early, so
  `acquisition_started >= deadline` holds on every tick) and drift by the
  summed jitter. Only a *counted* overrun (lateness > tolerance) rebases the
  next deadline to `acquisition_started + interval`. Consequences, stated
  precisely: after a counted overrun the next acquisition starts at least one
  interval after the late one — a temporary 300 ms stall at 10 Hz produces
  **no back-to-back catch-up burst** and no skipped ticks, the trace simply
  stretches; under merely-tolerated jitter, consecutive starts may be closer
  than one interval (bounded by the tolerance) as the loop returns to the
  nominal grid. (Rebase chosen over skip-missed-ticks because consumers get
  the sample count they asked for and the actual timestamps carry the truth.)
- **One `Signals.ValsGet` per tick** (never N × `ValGet`); the actual
  post-call `monotonic()` offset is recorded, not the nominal tick.
- **Response validation on every tick** (strict, per M5a-1): non-mapping,
  missing/non-integer/inconsistent `signals_values_size`, or array length ≠
  `n_signals` → `TimeTraceResponseError` (aborts the run — malformed data
  must not be silently truncated into a "valid" trace).
- **Transport failure** (`NanonisTimeoutError` etc.) on any tick aborts and
  propagates — the partial-data path is *only* the deliberate token cancel.
- **Early stop** (token): arrays truncated to the acquired count,
  `cancelled=True`.
- **After the loop**: apply `nan_policy` via `inspect_non_finite_trace` —
  WARN logs diagnostics, RAISE raises
  `NonFiniteTimeTraceDataError(result, diagnostics)` *retaining the result*,
  ALLOW does nothing (mirroring the spectroscopy/scan behaviour with a
  trace-specific inspector).
- Progress events every ~1 s.

`workflows/datalog/__init__.py` + `workflows/__init__.py` export
`TimeTraceConfig`, `TimeTraceResult`, `TimeTraceWorkflow`,
`TimeTraceResponseError`, `NonFiniteTimeTraceDataError`.

**FakeController tests** (`tests/workflows/datalog/test_time_trace.py`):

- happy path: scripted `ValsGet` mapping responses → shapes, strictly
  increasing `elapsed_s`, `sent` shows only read commands, correct
  `wait_flag` wire value and index-size argument;
- malformed `ValsGet` responses: non-mapping; missing `signals_values`;
  missing, non-integer, or inconsistent `signals_values_size`; array wrong
  length (both short and long) → `TimeTraceResponseError`, no partial result;
- malformed `NamesGet`: `signals_names_number` ≠ array length; a requested
  index ≥ `signals_names_number` → `TimeTraceResponseError`;
- name resolution on/off (scripted `NamesGet`, including duplicate names);
- accessor behaviour: `signal_by_index` / `signal_by_name` happy paths,
  KeyError on unknown index, ValueError on unresolved/missing/ambiguous name;
- cancel mid-run → truncated partial result, `cancelled=True`, no exception;
  cancel while *late* (fake controller that sleeps) → still observed;
- timeout on tick 3 → propagates, first 2 samples not silently returned;
- config validation matrix (each invalid field → `ValueError`), including the
  element/memory cap, duration semantics (1 s / 1 s → 2 samples), and the
  float-safe count (`0.3 s / 0.1 s → 4`, `0.35 / 0.1 → 4`, `60 / 0.1 → 601`);
- `nan_policy`: WARN logs and returns; RAISE raises
  `NonFiniteTimeTraceDataError` with the result attached; ALLOW silent;
- lateness accounting with a fake controller that sleeps: sample 0 never
  late; late counted only beyond tolerance; a scripted *sleep overshoot*
  (slow `cancel.wait` double) is counted;
- rebase-only-after-counted-overrun: after a scripted stall (lateness >
  tolerance), the next acquisition start is ≥ one interval after the late one
  (no burst); under scripted sub-tolerance jitter the nominal grid is
  preserved — assert the final deadline equals `t0 + (n-1) * interval` (no
  drift accumulation);
- `Util.VersionGet` raising `NanonisCommandError` → `nanonis_version is
  None`, acquisition proceeds; raising `NanonisTimeoutError` → propagates,
  no samples acquired.

## M5a-4 — Live acceptance

Script: `examples/live_time_trace.py` (pattern of `verify_waitendofline.py`),
using `cancel_on_sigint`. Gate — all must pass on the real rig, results
recorded in a dated live report:

1. 60 s trace of the Z slot (and current) at 10 Hz (601 samples), feedback
   **on**: `late_sample_count <= 6` (1 % of 601);
2. timing: `elapsed_s[-1]` within [60.0 s, 60.6 s] (nominal span, ≤ 1 %
   stretch); 95th percentile of `|diff(elapsed_s) - 0.1| <= 0.02 s` (20 % of
   the interval), with `wait_for_newest_data` as chosen in M5a-1;
3. cross-check *outside* the timed loop (never interleaved into it — the
   sequential extra round-trip would corrupt the timing under test): ~10
   alternating `ValsGet`/`ZCtrl.ZPosGet` reads of the Z slot immediately
   before and after the timed trace, agreeing within float32 quantization of
   the live Z excursion;
4. first Ctrl-C mid-trace (SIGINT → token) returns the truncated partial
   result with `cancelled=True`;
5. before/after snapshots of bias, setpoint, feedback, RT settings are
   **identical** (proves the mutates-nothing claim).

## Extension points (designed for, not built)

- **Alternative backends.** When a real use case needs kHz-rate traces
  (noise spectra, time-resolved signals), add a TCPLog streaming backend: same
  `TimeTraceConfig` + `TimeTraceResult`, a different acquisition strategy
  behind the workflow (e.g. a `backend` config field or a sibling workflow
  class). The result model already carries everything a streaming backend
  produces; nothing in the polling design blocks it. TCPLog first needs its
  own live validation (separate stream port, second reader socket). The
  file-based Data Logger group (`DataLog.json`, transcribed 2026-07-02) is a
  third candidate backend for long unattended logs that Nanonis itself should
  own — equally deferred, equally live-unvalidated.
- **Module-specific reader strategies.** If a consumer ever needs a channel
  the Signals bus does not expose well, the extension is a per-signal *reader
  strategy* (a different Get command per slot), not a flag on `ValsGet` —
  though note that the known module getters are also float32, so this buys
  provenance, not precision.
- **Derived-quantity helpers** (PSD/noise floor, Allan deviation, settling
  detection) belong in a pure analysis module *consuming* `TimeTraceResult` —
  never inside the workflow.
- **xarray / QCoDeS adapters** for traces follow the established
  acquire-first adapter pattern if ever needed; dormant by policy.

## Module/test layout

```text
src/nanonis/
  provenance.py                         # M5a-2: neutral package-version/git-commit
                                        #   helper hoisted from data/_utils.py
src/nanonis/workflows/
  cancellation.py                       # M5a-0 (incl. cancel_on_sigint)
  datalog/{__init__,models,result,workflow}.py    # M5a-2/3
configs/commands/Signals.json           # ValsGet: verify vs PDF + commit (M5a-1)
tests/workflows/
  test_cancellation.py
  datalog/test_time_trace.py
examples/
  characterize_signals.py               # M5a-1
  live_time_trace.py                    # M5a-4
```

Suggested commit slices = the milestone numbers (each lands green: code +
tests + exports + doc touch).

## Open questions (resolve at the marked milestone)

1. `wait_for_newest_data` default and the real polling-rate floor — **M5a-1**,
   from measured latency.
2. Float32 adequacy — **M5a-1**. *All* signal reads are float32 on the wire
   (`ValGet`, `ValsGet`, and `ZCtrl.ZPosGet` alike — there is no float64
   path). Estimate: Z ≈ 10⁻⁷ m scale × float32 relative epsilon ≈ 10⁻¹⁴ m
   quantization ≈ 10 fm, comfortably below pm-scale drift structure — but
   *measure* the observed quantization step on the live Z slot and record it.
   If a future consumer genuinely exceeds float32, that is a new backend
   discussion (TCPLog/DataLog file paths), not a polling option.
3. `signals_indexes_size` prefix: element count or byte count — **M5a-1**,
   from the PDF + a live call with ≥ 2 indexes (a wrong guess fails loudly as
   a protocol error, which is itself the test).

## Non-goals (M5a)

- TCPLog / Data Logger backends (deferred; see Extension points — both groups
  are transcribed but live-unvalidated).
- Setting tunnel conditions around a trace (tunnel vertical, lab-policy
  blocked).
- Any analysis of the acquired trace — including drift fitting, which lives
  entirely in the drift vertical ([`drift_plan.md`](drift_plan.md)).
- QCoDeS persistence (dormant by policy; `to_metadata()` keeps the door open).

## References

- [`blueprint.md`](blueprint.md) — vision, backlog, milestone ordering.
- [`drift_plan.md`](drift_plan.md) — the first consumer of this vertical.
- `spaik/src/spaik/SPMMeasurement.py` — `doDataLogging` (l. 6850): the recipe
  and the defect catalogue (condition-setting conflation, sleep-and-reread).
- `TCPProtocol_SPM.pdf` — §Signals (ValsGet verification).
- [`data_readers_plan.md`](data_readers_plan.md) — the other reduced-shape
  (read-only) vertical this one mirrors.
