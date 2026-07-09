# Datalog Live View — Implementation Walkthrough

Implemented: 2026-07-02

## Outcome

The datalog workflow can now publish every stored sample to a trusted consumer,
and the package provides a complete Matplotlib-free hand-off and lifecycle
layer for displaying those samples from another thread. The acquisition result,
scheduling, validation, NaN policy, and read-only controller command sequence
remain unchanged when no sample callback is supplied.

Rendering stays in `examples/live_trace_view.py`. The workflow package does not
import Matplotlib.

## Sample delivery

`SampleEvent` is an immutable event containing the workflow name, zero-based
sample index, stored elapsed time, and an immutable tuple of signal values.
`TimeTraceWorkflow.run()` accepts `on_sample=` and dispatches immediately after
the corresponding row is written to the acquisition buffers. Consequently the
event timestamps and values exactly match the returned `TimeTraceResult`, and a
cancelled tick that stores no sample emits no event.

The callback runs synchronously in the acquisition thread. A conforming callback
must only enqueue and return; it must not access the client or block. If it
raises, the workflow logs the first traceback, disables further sample delivery,
and continues acquisition. A single end-of-run warning identifies the sample at
which delivery stopped. That warning is emitted from `finally`, so a later
transport or NaN-policy exception does not suppress it.

With `on_sample=None`, the event construction branch is never entered. Tests
pin both zero event allocation and the unchanged command sequence.

## Inbox and display history

`SampleInbox` is the reference callback. Its `push()` operation locks only long
enough to append an event, dropping the oldest queued event if the configured
capacity is full. `drain()` atomically transfers all pending events to the UI,
and `dropped_count` is monotonic.

`TraceHistory` is owned by the UI thread. It applies the rolling time window and
an independent hard sample cap. A discontinuity in `sample_index` inserts a NaN
row between the surrounding samples, so overflow is shown as a line break rather
than a false connection.

`display_arrays()` returns elapsed time and a `(signals, points)` matrix. It
decimates only display data and always keeps non-finite rows and the newest
sample. The immutable workflow result is never modified. If mandatory NaN/gap
rows alone outnumber `max_points`, preserving those gaps takes precedence over
the display point limit because both constraints cannot be satisfied
simultaneously.

## Background lifecycle

`BackgroundTraceRun` has five states:

```text
NOT_STARTED -> RUNNING -> FINISHED
                       -> CANCELLED
                       -> FAILED
```

`start()` is single-use and non-blocking. The worker thread is deliberately
non-daemon because it owns an active command connection and the acquisition
result. `on_progress` is forwarded unchanged and, like `on_sample`, executes in
the worker thread.

`done` is read-only; `wait(timeout)` reports whether any terminal state was
reached. `result(timeout)` joins the worker, returns the same result object on
repeated calls, or re-raises the original worker exception. Calling it before
`start()` or calling `start()` twice is an error.

Cancellation delegates to the runner's `CancelToken`. It remains cooperative:
an in-flight `client.send()` cannot be interrupted. If a result wait expires,
`LiveViewTimeoutError` explicitly states that the worker is still running and
still owns the client. The caller must not reuse or close that client until
`run.done` becomes true. The runner never closes a client itself.

## Plot and text consumers

`examples/live_trace_view.py` contains `MatplotlibTraceView`. Its GUI timer:

1. drains the inbox into `TraceHistory`;
2. updates one line per signal and periodically autoscales;
3. displays runner state and the dropped-event count;
4. performs one final drain/redraw after `run.done`, then stops itself.

The Stop button only calls `run.cancel()`. In a notebook, use
`%matplotlib widget`; `view.start()` returns immediately and a later cell can
inspect `run.state`, call `run.wait()`, and retrieve `run.result()`.

`monitor_blocking()` is the explicit text fallback for missing Matplotlib or an
Agg/inline backend. It drains and prints the newest values until completion.
For scripts, `cancel_on_sigint(token)` must wrap the whole start/monitor/result
session. Notebook users should use the Stop button because a context wrapped
only around non-blocking `start()` would restore the SIGINT handler immediately.

The optional dependencies are available through:

```console
pip install -e .[liveview]
```

The existing datalog tutorial notebook now includes an opt-in widget-backend
live-view section and a separate later-cell result check.

## Verification

The focused tests cover ordered event/result equality, fail-once logging,
transport failure after callback failure, timing perturbation and the final
sample blind spot, cancellation cardinality, and the no-op invariant. They also
cover concurrent inbox use, overflow, rolling history, hard caps,
gap-preserving decimation, all runner terminal states, timeout ownership,
non-daemon threading, progress forwarding, repeated results, and final draining.

An Agg-backend smoke test drives the renderer tick directly and verifies line
updates, terminal labeling, and timer shutdown. No live controller test was run
during implementation.
