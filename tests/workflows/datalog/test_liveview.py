from __future__ import annotations

import threading

import numpy as np
import pytest

from nanonis.protocol import NanonisTimeoutError
from nanonis.workflows import (
    BackgroundTraceRun,
    CancelToken,
    LiveViewTimeoutError,
    RunState,
    SampleEvent,
    SampleInbox,
    TimeTraceConfig,
    TimeTraceWorkflow,
    TraceHistory,
)

from ..conftest import FakeController
from .test_time_trace import scripted_client, vals, version


def event(index: int, *values: float, elapsed: float | None = None) -> SampleEvent:
    return SampleEvent(
        "datalog.time_trace",
        index,
        float(index) if elapsed is None else elapsed,
        tuple(values),
    )


def test_inbox_concurrent_push_and_drain_has_no_loss_below_capacity() -> None:
    inbox = SampleInbox(500)
    received: list[SampleEvent] = []
    producer_done = threading.Event()

    def produce() -> None:
        for index in range(300):
            inbox.push(event(index, float(index)))
        producer_done.set()

    thread = threading.Thread(target=produce)
    thread.start()
    while not producer_done.is_set():
        received.extend(inbox.drain())
    thread.join()
    received.extend(inbox.drain())

    assert [item.sample_index for item in received] == list(range(300))
    assert inbox.dropped_count == 0


def test_inbox_overflow_drops_oldest() -> None:
    inbox = SampleInbox(3)
    for index in range(5):
        inbox.push(event(index, float(index)))
    assert [item.sample_index for item in inbox.drain()] == [2, 3, 4]
    assert inbox.dropped_count == 2


def test_history_window_cap_and_discontinuity_gap() -> None:
    history = TraceHistory(1, window_s=2.0, max_history_samples=10)
    history.extend([event(0, 0.0), event(1, 1.0), event(4, 4.0)])
    elapsed, values = history.display_arrays()
    assert elapsed[0] >= 2.0
    assert np.isnan(values).any()
    assert values[0, -1] == 4.0

    capped = TraceHistory(1, window_s=None, max_history_samples=3)
    capped.extend([event(index, float(index)) for index in range(5)])
    capped_elapsed, _ = capped.display_arrays()
    np.testing.assert_array_equal(capped_elapsed, [2.0, 3.0, 4.0])


def test_history_decimation_preserves_nan_rows_and_final_sample() -> None:
    history = TraceHistory(2, window_s=None, max_points=5)
    events = [event(index, float(index), float(index)) for index in range(12)]
    events[3] = event(3, float("nan"), 3.0)
    history.extend(events[:7] + [event(9, 9.0, 9.0), *events[10:]])
    elapsed, values = history.display_arrays()

    assert elapsed.size <= 5
    assert 3.0 in elapsed
    assert any(np.all(np.isnan(values[:, column])) for column in range(values.shape[1]))
    assert elapsed[-1] == 11.0
    assert values[0, -1] == 11.0


def test_background_run_completes_and_final_drain_matches_result() -> None:
    inbox = SampleInbox(20)
    run = BackgroundTraceRun(
        TimeTraceWorkflow(scripted_client(3)),
        TimeTraceConfig(
            (0,), duration_s=0.08, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=inbox,
    )
    assert not run._thread.daemon
    assert not run.wait(0.001)
    run.start()
    first = inbox.drain()
    assert run.wait(1.0)
    final = first + inbox.drain()
    result = run.result()

    assert run.state is RunState.FINISHED
    assert [item.sample_index for item in final] == list(range(result.n_samples))
    assert run.result() is result


def test_background_run_cancellation_returns_partial_result() -> None:
    token = CancelToken()
    inbox = SampleInbox(20)
    first_read = threading.Event()
    client = FakeController().script("Util.VersionGet", version())

    def response(command, args, timeout):
        first_read.set()
        return vals(1.0)

    client.script("Signals.ValsGet", *(response for _ in range(11)))
    run = BackgroundTraceRun(
        TimeTraceWorkflow(client),
        TimeTraceConfig(
            (0,), duration_s=0.4, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=inbox,
        cancel=token,
    )
    run.start()
    assert first_read.wait(1.0)
    run.cancel()
    result = run.result(1.0)
    assert result.cancelled
    assert result.n_samples < 11
    assert run.state is RunState.CANCELLED


def test_background_run_failure_is_re_raised() -> None:
    error = NanonisTimeoutError("timeout")
    client = FakeController().script("Util.VersionGet", version())
    client.fail("Signals.ValsGet", error)
    run = BackgroundTraceRun(
        TimeTraceWorkflow(client),
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=SampleInbox(10),
    )
    run.start()
    assert run.wait(1.0)
    with pytest.raises(NanonisTimeoutError) as caught:
        run.result()
    assert caught.value is error
    assert run.state is RunState.FAILED


def test_background_run_rejects_result_before_start_and_double_start() -> None:
    run = BackgroundTraceRun(
        TimeTraceWorkflow(scripted_client(2)),
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=SampleInbox(10),
    )
    with pytest.raises(RuntimeError, match="not been started"):
        run.result()
    run.start()
    with pytest.raises(RuntimeError, match="single-use"):
        run.start()
    run.result(1.0)


def test_background_timeout_leaves_running_worker_until_client_unblocks() -> None:
    entered = threading.Event()
    release = threading.Event()
    client = FakeController().script("Util.VersionGet", version())

    def blocked(command, args, timeout):
        entered.set()
        release.wait(2.0)
        return vals(1.0)

    client.script("Signals.ValsGet", blocked, vals(2.0))
    run = BackgroundTraceRun(
        TimeTraceWorkflow(client),
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=SampleInbox(10),
    )
    run.start()
    assert entered.wait(1.0)
    with pytest.raises(LiveViewTimeoutError, match="still owns the client"):
        run.result(0.001)
    assert run.state is RunState.RUNNING
    assert not run.done
    release.set()
    assert run.result(1.0).n_samples == 2


def test_progress_callback_runs_in_worker_thread() -> None:
    callback_threads: list[int] = []
    main_thread = threading.get_ident()
    run = BackgroundTraceRun(
        TimeTraceWorkflow(scripted_client(2)),
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=SampleInbox(10),
        on_progress=lambda update: callback_threads.append(threading.get_ident()),
    )
    run.start()
    run.result(1.0)
    assert callback_threads
    assert set(callback_threads) != {main_thread}
