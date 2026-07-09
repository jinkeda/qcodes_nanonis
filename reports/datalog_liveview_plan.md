# Datalog Live View — Proposal (M5a-LV)

Status: proposal, rev. 3 (round 2 resolved: gap-preserving decimation,
non-daemon worker, `done`/`wait()` instead of a mutable Event, `on_progress`
forwarding, fail-once summary from `finally`, conforming-consumer qualifier,
`LiveViewTimeoutError` placed in `workflows/errors.py`. Round 1: consumer
contract, lifecycle, fail-once dispatcher, tested view model, inbox/history
separation, control flow, `liveview` extra, testable no-op invariant) ·
Date: 2026-07-02
Scope: an oscilloscope-style **live view** of a running time trace — per-sample
event delivery from `TimeTraceWorkflow` plus a decoupled display consumer.
Milestones: LV0 (event hook), LV1a (matplotlib-free view model + background
runner, fully tested), LV1b (matplotlib shell + notebook section). Rolling
"monitor forever" mode, kHz waveforms, and alternative backends stay deferred
(see Non-goals).

Parent: [`datalog_plan.md`](datalog_plan.md) (the vertical this extends) and
[`datalog_walkthrough.md`](datalog_walkthrough.md) (what is built). This
proposal adds an **observer**, not a backend: the config, result model,
scheduling, validation, and NaN semantics of the vertical stay unchanged.

## What the architecture provides — and what it cannot

Genuinely provided today:

- The workflow mutates no hardware state and returns an immutable result, so
  a **conforming** display consumer (per the contract below) cannot alter
  *what* is measured. A non-conforming callback can — it runs in the
  acquisition thread with the client in scope — which is why the contract
  exists.
- `CancelToken` is thread-safe (built for M6): acquisition in a worker
  thread, `token.cancel()` from the UI thread, partial trace with
  `cancelled=True` — the existing contract.
- Actual timestamps + `late_sample_count` report scheduling perturbation for
  every sample **that has a successor**.

Explicitly *not* provided — the consumer contract:

- **`on_sample` runs synchronously in the acquisition thread.** Arbitrary
  callback code can block acquisition indefinitely, touch the client
  mid-protocol, or perturb timing. No mechanism prevents this; the contract
  *requires* trusted consumers to (a) never touch the client, (b) never
  block, (c) do nothing but enqueue-and-return (microseconds). LV1a's
  `SampleInbox.push` is the reference implementation of a conforming
  callback.
- Lateness accounting detects a slow consumer only via the *next* sample's
  deadline — a slow callback on the **final** sample is invisible to
  `late_sample_count`. Stated here so nobody reads the counter as a proof of
  non-perturbation; the with/without-viewer acceptance comparison (below) is
  the actual evidence.

## Design rules

- **The live view is a consumer, never a backend.** No change to
  `TimeTraceConfig`, `TimeTraceResult`, scheduling, validation, or NaN
  policy. The no-op invariant is testable, not rhetorical: with
  `on_sample=None` the command sequence, result schema, NaN behaviour, and
  scheduling semantics are identical and **no event objects are allocated**.
- **No matplotlib inside `nanonis.workflows`.** The package gains only
  matplotlib-free code (events, inbox, history model, background runner);
  rendering lives in `examples/`. Mixing plotting into measurement code is
  the `spaik` anti-pattern this rebuild removed.
- **Ingress and display history are separate stores.** A drained queue cannot
  also be the rolling window. Producer → bounded **inbox** (drop-oldest with
  a dropped counter) → UI-owned **history** (rolling window, display
  decimation). Dropped or missing samples are *rendered as gaps*, never
  silently connected by a line.
- **One connection, one workflow.** While a trace runs, the worker thread
  owns the client; the UI thread may only call `token.cancel()`. The caller
  who created the client remains responsible for closing it — the runner
  never does. Concurrent monitoring during other measurements is the M6
  second-port pattern, not a locking scheme.
- **Events carry decoupled values** (`tuple[float, ...]`) — immutable, no
  aliasing of workflow buffers.
- No asyncio; one daemon thread and a GUI timer are the entire concurrency
  requirement.

## LV0 — `SampleEvent` + `on_sample` (workflow addition)

```python
# workflows/cancellation.py (event lives beside ProgressEvent)
@dataclass(frozen=True)
class SampleEvent:
    workflow: str                 # "datalog.time_trace"
    sample_index: int             # 0-based acquisition index
    elapsed_s: float              # the same value stored in the result
    values: tuple[float, ...]     # one float per configured signal, in order

SampleCallback = Callable[[SampleEvent], None]
```

```python
# TimeTraceWorkflow.run gains one keyword (backward-compatible):
def run(self, config, *, cancel=None, on_progress=None,
        on_sample: SampleCallback | None = None) -> TimeTraceResult: ...
```

Semantics:

- Dispatched once per **stored** sample, immediately after the buffer write
  (event `elapsed_s` equals the result's value, including the `np.nextafter`
  tie-break). Never fired for a tick that broke on cancellation; the final
  stored sample does fire.
- **Fail-once dispatcher — not `report_progress`.** A per-sample callback
  that fails persistently would otherwise log one traceback per sample (tens
  of Hz of logging I/O *inside the acquisition thread* — perturbation caused
  by the isolation mechanism itself). Instead, a sample-specific dispatcher:
  the first exception is logged with traceback and **disables the callback
  for the remainder of the run**; a single summary line reporting the sample
  index at which delivery stopped is emitted **from a `finally`**, so a later
  acquisition or NaN-policy exception cannot mask it. Progress events keep
  their existing (low-rate) dispatcher.
- Values converted with `tuple(float(v) for v in row)` — microseconds at
  this vertical's channel counts and rates; no batching at this layer (a
  consumer decimates for display; the workflow reports every sample it
  stores).
- `nan_policy` untouched: events carry raw acquired values (NaN included —
  rendered as a gap downstream), the policy still applies once to the
  assembled result.

**Tests** (`tests/workflows/datalog/test_time_trace.py` additions):

- events arrive in order, `sample_index` 0..n-1, exactly matching the
  returned result's `elapsed_s`/`values` columns;
- fail-once: a callback raising at sample 2 is disabled — exactly one
  traceback log + one end-of-run summary, no calls after sample 2,
  acquisition completes, result intact;
- fail-once summary survives later failures: callback fails at sample 2,
  then a scripted transport error at sample 4 → the exception propagates
  *and* the summary line was still emitted (`finally` path);
- a slow `on_sample` (FakeClock advance beyond tolerance inside the
  callback) → `late_sample_count` rises — and a slow callback on the *final*
  sample does **not** (pinning the documented blind spot);
- cancel mid-run → number of events equals `result.n_samples`;
- `values` is a tuple (type-checked);
- **no-op invariant**: with `on_sample=None`, the command sequence is
  identical to a run without the parameter and the event constructor is
  never invoked (e.g. patched counter).

Estimated size: ~40 lines of source, ~90 lines of tests.

## LV1a — View model + background runner (package, matplotlib-free, tested)

`workflows/datalog/liveview.py`. This is concurrency/lifecycle code — riskier
than LV0 — so it lives in the tested package layer, not in an example. It
imports nothing from matplotlib.

```python
class SampleInbox:
    """Thread-safe bounded producer→UI hand-off. `push` is the conforming
    on_sample callback: append-or-drop-oldest and return; nothing else."""
    def __init__(self, maxlen: int) -> None: ...
    def push(self, event: SampleEvent) -> None: ...       # acquisition thread
    def drain(self) -> list[SampleEvent]: ...             # UI thread
    @property
    def dropped_count(self) -> int: ...                   # monotonic counter

class TraceHistory:
    """UI-owned rolling display history. Not thread-safe; UI thread only."""
    def __init__(self, n_signals: int, *,
                 window_s: float | None = 60.0,
                 max_history_samples: int = 100_000,      # hard cap even when
                 max_points: int = 2000) -> None: ...     #   window_s is None
    def extend(self, events: list[SampleEvent]) -> None:
        # Detects sample_index discontinuities (inbox overflow) and inserts a
        # NaN row so plots show a gap instead of bridging dropped data.
        ...
    def display_arrays(self) -> tuple[FloatArray, FloatArray]:
        # (elapsed, values) trimmed to the window and decimated to
        # <= max_points. Decimation is GAP-PRESERVING: naive striding could
        # discard inserted gap rows, real NaNs, and the newest point. The
        # decimator always retains (a) every non-finite marker row and
        # (b) the final sample, striding only the finite runs between them.
        # Display-only; the workflow result is never touched.
        ...

class BackgroundTraceRun:
    """Single-use lifecycle wrapper: NOT_STARTED → RUNNING → (FINISHED |
    FAILED | CANCELLED). Owns the worker thread; never owns the client.

    The worker is a NON-daemon thread: it holds an active socket and the
    acquisition result, so interpreter exit must wait for it rather than
    abandon a socket mid-frame. Bounded command timeouts keep that wait
    finite under all normal and error paths."""
    def __init__(self, workflow: TimeTraceWorkflow, config: TimeTraceConfig,
                 *, inbox: SampleInbox, cancel: CancelToken | None = None,
                 on_progress: ProgressCallback | None = None) -> None: ...
        # on_progress is forwarded to workflow.run() — owning the run() call
        # must not remove an existing API capability. Note: it executes in
        # the WORKER thread; the same trusted-consumer contract applies.
    def start(self) -> None:                  # non-blocking; RuntimeError on reuse
    @property
    def state(self) -> RunState: ...
    @property
    def done(self) -> bool: ...               # True on any terminal state
    def wait(self, timeout: float | None = None) -> bool:
        # Block until terminal (True) or timeout (False). No mutable
        # threading.Event is exposed — callers cannot corrupt lifecycle
        # state by calling set().
        ...
    def cancel(self) -> None: ...               # delegates to the token
    def result(self, timeout: float | None = None) -> TimeTraceResult:
        # Joins the worker. On FINISHED/CANCELLED returns the (possibly
        # partial) result; on FAILED re-raises the worker's exception in the
        # caller's thread. On join timeout raises LiveViewTimeoutError *while
        # the worker still runs and still owns the client* — see lifecycle.
        ...
```

`LiveViewTimeoutError` lives in `workflows/errors.py` beside the other
workflow errors and is exported from `nanonis.workflows` (resolved — was an
open question in rev. 2).

**Lifecycle contract (the honest part):** cancellation is cooperative and
checked *between* commands — it cannot interrupt an in-flight
`client.send()`. Therefore:

- the worst-case latency from `cancel()` to `finished` is one command's
  socket timeout, and callers of `result(timeout=...)` must size the timeout
  accordingly;
- a `LiveViewTimeoutError` means the worker is **still running and still owns
  the client** — the caller must neither reuse nor close the client until
  `finished` is set (the error message says so);
- `start()` is single-use (`RuntimeError` on a second call, and on
  `result()` before `start()`);
- the runner never closes the client; whoever constructed it does, after
  `finished`.

**Tests** (`tests/workflows/datalog/test_liveview.py`, FakeController +
FakeClock, no GUI):

- concurrent push/drain from two threads: no loss below capacity; overflow
  drops oldest and increments `dropped_count`;
- `TraceHistory`: window trimming, `max_history_samples` cap with
  `window_s=None`, NaN gap row inserted at a `sample_index` discontinuity;
- **gap-preserving decimation**: with dense data above `max_points`, the
  decimated arrays retain every gap/NaN marker row and the final sample
  (construct a history whose naive stride would drop both, assert they
  survive);
- final drain: events pushed after the last UI drain are still delivered by
  a drain performed after `done` becomes true;
- `BackgroundTraceRun`: completed run returns the same result the workflow
  produced; cancel → CANCELLED with partial result; worker exception
  (scripted `NanonisTimeoutError`) → FAILED and re-raised from `result()`;
  `result()` before `start()` and double `start()` → RuntimeError;
  `result(timeout)` against a hung fake client → `LiveViewTimeoutError`,
  state still RUNNING, then clean join once the fake unblocks;
- `done`/`wait()`: `wait(0.01)` returns False while running, True after any
  terminal state; the worker thread is non-daemon (asserted);
- `on_progress` forwarding: a progress callback passed to the runner is
  invoked by the workflow (scripted long run), from the worker thread;
- repeated `result()` after completion returns the same object.

## LV1b — Matplotlib shell + notebook section (example layer)

`examples/live_trace_view.py` — a thin rendering shell over LV1a; all logic
already tested lives in the package:

- a matplotlib timer (`fig.canvas.new_timer`, `redraw_hz` ≈ 5) whose tick is:
  `history.extend(inbox.drain())` → update `Line2D` data → throttled
  autoscale; when `run.done` becomes true, perform **one final drain +
  redraw, then stop the timer**;
- a Stop widget wired to `run.cancel()`; the figure title shows state and
  the dropped-event counter;
- **control flow**: `start()` returns immediately; the notebook cell that
  started the run ends, the plot keeps updating via the GUI timer, and
  completion is observed via `run.state` / `run.wait(timeout)` — a later
  cell calls `run.result()` (documented as potentially blocking up to one
  socket timeout);
- **Ctrl-C strategy**: notebooks use the Stop widget (SIGINT in Jupyter
  interrupts the *cell*, and a `cancel_on_sigint` inside `start()` would be
  restored the moment `start()` returned — so it is not used here). Scripts
  wrap their whole session: `with cancel_on_sigint(token): run.start();
  run.result()`;
- **text fallback**: no GUI timer exists, so the fallback is an explicit
  blocking loop in the caller's thread — `monitor_blocking(run, inbox,
  poll_interval=1.0)` drains, prints last values + dropped count, and exits
  when `run.done` becomes true (Ctrl-C lands in this loop and cancels via
  the script-level `cancel_on_sigint`);
- **smoke test**: one Agg-backend test (`pytest.importorskip("matplotlib")`)
  drives the timer tick function directly against a scripted run and asserts
  lines/labels update and the timer stops — kept in the normal suite, skipped
  where matplotlib is absent.

**Dependencies (explicit):** new optional extra in `pyproject.toml` —
`liveview = ["matplotlib>=3.8", "ipympl>=0.9"]` — imported lazily. Fallback
activation is defined, not vibes: matplotlib missing → text monitor;
matplotlib present but the active backend is non-interactive (Agg/`inline`)
→ warn naming the backend, then text monitor. The notebook section states
that `%matplotlib widget` (ipympl) is required for live updates.

## Live acceptance (piggybacks on the M5a-4 rig session)

1. Live view of the 60 s / 10 Hz acceptance trace renders smoothly (≥ 5 fps
   subjective) while the trace completes; dropped-event counter stays 0.
2. **Non-perturbation is measured, not assumed**: run the acceptance trace
   with and without the viewer; `late_sample_count` and p95 interval error
   stay within the M5a-4 gates in both runs.
3. Stop button mid-trace → CANCELLED, partial result, timer stopped after
   the final drain; `run.done` true and the (non-daemon) worker joined
   within one socket timeout.
4. A NaN in the live data renders as a gap, not a crash.

## Non-goals (deferred, with their upgrade paths)

- **Rolling "monitor forever" mode** — `TimeTraceConfig` is fixed-count by
  design. Phase 1 sidesteps it: start a long bounded trace and cancel when
  done (partial results are valid). A ring-buffer monitor (no final result)
  would be a small sibling workflow later.
- **kHz waveforms** — polling cannot do it. Catalogued upgrade paths: the
  TCPLog streaming backend (separate stream port, second reader socket) and
  the Nanonis oscilloscope modules (`Osci1T`/`Osci2T`/`OsciHR`/
  `SignalChart`, already in `configs/commands`) whose trigger-then-block-
  fetch pattern gives hardware-timed waveforms over the existing command
  port.
- **Concurrent monitoring during other measurements** — second-port client,
  M6 pattern.
- **A `nanonis/viz` package** — premature until a second rendering consumer
  exists.
- **Event batching** (`on_samples(list)`) — only if a future backend raises
  rates enough that per-sample dispatch matters; not at ≤ tens of Hz.

## Open questions

None blocking. Rev.-2 questions resolved: `LiveViewTimeoutError` lives in
`workflows/errors.py` and is exported publicly (see LV1a); ipympl
availability on the lab PCs does not gate implementation because the
fallback behaviour is fully specified — it only decides which mode the
notebook section demonstrates first.

## References

- [`datalog_plan.md`](datalog_plan.md) — the vertical (rev. 5) this extends;
  its Extension points section points here.
- [`datalog_walkthrough.md`](datalog_walkthrough.md) — implemented state,
  including the blocking `client.send()` this lifecycle contract is honest
  about.
- [`drift_plan.md`](drift_plan.md) — M6 background pattern (second-port
  client) referenced by the concurrency rule.
