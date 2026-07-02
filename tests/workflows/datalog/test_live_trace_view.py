from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from nanonis.workflows import (
    BackgroundTraceRun,
    RunState,
    SampleEvent,
    SampleInbox,
    TimeTraceConfig,
    TimeTraceWorkflow,
)

from .test_time_trace import scripted_client


def load_example_module():
    example_path = Path(__file__).parents[3] / "examples" / "live_trace_view.py"
    spec = importlib.util.spec_from_file_location("live_trace_view", example_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_agg_view_tick_updates_lines_and_stops_timer() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    module = load_example_module()

    inbox = SampleInbox(20)
    run = BackgroundTraceRun(
        TimeTraceWorkflow(scripted_client(3)),
        TimeTraceConfig(
            (0,), duration_s=0.08, sample_interval_s=0.04, resolve_names=False
        ),
        inbox=inbox,
    )
    view = module.MatplotlibTraceView(run, inbox, ("signal",))
    stop_calls = 0
    original_stop = view.timer.stop

    def record_stop() -> None:
        nonlocal stop_calls
        stop_calls += 1
        original_stop()

    view.timer.stop = record_stop
    try:
        view.start()
        assert run.wait(1.0)
        assert view.tick() is False
        assert len(view.lines[0].get_xdata()) == 3
        assert "finished" in view.figure._suptitle.get_text()
        assert stop_calls == 1
    finally:
        plt.close(view.figure)


def test_tick_does_not_stop_when_worker_finishes_during_drain() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    module = load_example_module()

    class RacingRun:
        done = False

        @property
        def state(self) -> RunState:
            return RunState.FINISHED if self.done else RunState.RUNNING

        def cancel(self) -> None:
            pass

    run = RacingRun()

    class RacingInbox(SampleInbox):
        def __init__(self) -> None:
            super().__init__(10)
            self.push(SampleEvent("datalog.time_trace", 0, 0.0, (1.0,)))
            self.raced = False

        def drain(self) -> list[SampleEvent]:
            drained = super().drain()
            if not self.raced:
                self.push(SampleEvent("datalog.time_trace", 1, 0.1, (2.0,)))
                run.done = True
                self.raced = True
            return drained

    inbox = RacingInbox()
    view = module.MatplotlibTraceView(run, inbox, ("signal",))
    try:
        assert view.tick() is True
        assert list(view.lines[0].get_ydata()) == [1.0]
        assert view.tick() is False
        assert list(view.lines[0].get_ydata()) == [1.0, 2.0]
    finally:
        plt.close(view.figure)
