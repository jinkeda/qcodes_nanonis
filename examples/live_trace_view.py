"""Oscilloscope-style live view for :class:`TimeTraceWorkflow`.

In notebooks, select ``%matplotlib widget`` before constructing the view. The
plotting dependency is optional; a blocking text monitor is provided for
headless and non-interactive backends.
"""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
if not (ROOT / "src" / "nanonis").exists():  # pragma: no cover - import guard
    raise RuntimeError("Run from the repository root or examples directory")
sys.path.insert(0, str(ROOT / "src"))

from nanonis.command import NanonisController  # noqa: E402
from nanonis.workflows import (  # noqa: E402
    BackgroundTraceRun,
    CancelToken,
    RunState,
    SampleInbox,
    TimeTraceConfig,
    TimeTraceWorkflow,
    TraceHistory,
    cancel_on_sigint,
)


class MatplotlibTraceView:
    """Thin Matplotlib renderer over the tested live-view package objects."""

    def __init__(
        self,
        run: BackgroundTraceRun,
        inbox: SampleInbox,
        signal_labels: Sequence[str],
        *,
        redraw_hz: float = 5.0,
        window_s: float | None = 60.0,
        max_points: int = 2000,
    ) -> None:
        if redraw_hz <= 0:
            raise ValueError("redraw_hz must be positive")
        if not signal_labels:
            raise ValueError("signal_labels must not be empty")

        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button

        self.run = run
        self.inbox = inbox
        self.history = TraceHistory(
            len(signal_labels), window_s=window_s, max_points=max_points
        )
        self.figure, axes = plt.subplots(
            len(signal_labels), 1, sharex=True, squeeze=False
        )
        self.axes = tuple(axes[:, 0])
        self.lines = []
        for axis, label in zip(self.axes, signal_labels):
            (line,) = axis.plot([], [], lw=1.0)
            axis.set_ylabel(label)
            axis.grid(alpha=0.3)
            self.lines.append(line)
        self.axes[-1].set_xlabel("elapsed (s)")
        self.figure.subplots_adjust(bottom=0.14)
        stop_axis = self.figure.add_axes((0.82, 0.02, 0.12, 0.06))
        self.stop_button = Button(stop_axis, "Stop")
        self.stop_button.on_clicked(lambda event: self.run.cancel())

        self.timer = self.figure.canvas.new_timer(
            interval=max(1, round(1000.0 / redraw_hz))
        )
        self.timer.add_callback(self.tick)
        self._autoscale_every = max(1, round(redraw_hz))
        self._ticks = 0
        self._terminal_drawn = False

    def start(self) -> None:
        """Start the worker and GUI timer, then return immediately."""
        self.run.start()
        self.timer.start()
        self.figure.canvas.draw_idle()

    def tick(self) -> bool:
        """Drain, redraw, and stop after one final terminal-state drain."""
        if self._terminal_drawn:
            return False

        # Snapshot completion before draining. Once done is observable, every
        # producer push has completed, so this drain is provably final. If the
        # worker finishes during the drain, one more timer tick performs it.
        done = self.run.done
        self.history.extend(self.inbox.drain())
        elapsed, values = self.history.display_arrays()
        for index, line in enumerate(self.lines):
            line.set_data(elapsed, values[index])

        self._ticks += 1
        if elapsed.size and (self._ticks % self._autoscale_every == 0 or done):
            for axis in self.axes:
                axis.relim()
                axis.autoscale_view()
        self.figure.suptitle(
            f"{self.run.state.value} — dropped events: {self.inbox.dropped_count}"
        )
        self.figure.canvas.draw_idle()

        if done:
            self._terminal_drawn = True
            self.timer.stop()
            return False
        return True


def interactive_matplotlib_available() -> bool:
    """Return whether Matplotlib is installed with an interactive backend."""
    try:
        import matplotlib
    except ImportError:
        return False
    backend = str(matplotlib.get_backend()).lower()
    non_interactive = "agg" in backend or "inline" in backend
    if non_interactive:
        warnings.warn(
            f"Matplotlib backend {matplotlib.get_backend()!r} is not interactive; "
            "using the blocking text monitor",
            RuntimeWarning,
            stacklevel=2,
        )
    return not non_interactive


def monitor_blocking(
    run: BackgroundTraceRun,
    inbox: SampleInbox,
    *,
    poll_interval: float = 1.0,
) -> None:
    """Drain and print samples until a previously started run terminates."""
    if poll_interval <= 0:
        raise ValueError("poll_interval must be positive")
    while True:
        events = inbox.drain()
        if events:
            latest = events[-1]
            print(
                f"sample={latest.sample_index} elapsed={latest.elapsed_s:.3f}s "
                f"values={latest.values} dropped={inbox.dropped_count}",
                flush=True,
            )
        if run.done:
            # An event may arrive between the drain and the terminal-state read.
            events = inbox.drain()
            if events:
                latest = events[-1]
                print(
                    f"sample={latest.sample_index} elapsed={latest.elapsed_s:.3f}s "
                    f"values={latest.values} dropped={inbox.dropped_count}",
                    flush=True,
                )
            return
        time.sleep(poll_interval)


def main() -> int:  # pragma: no cover - live example
    host, port = "127.0.0.1", 6504
    signal_indexes = (0, 1)  # Replace with the rig's Z and current slots.
    client = NanonisController(
        host=host,
        port=port,
        config_path=ROOT / "configs" / "commands",
        timeout=10.0,
    )
    client.connect()
    token = CancelToken()
    inbox = SampleInbox(maxlen=10_000)
    run = BackgroundTraceRun(
        TimeTraceWorkflow(client),
        TimeTraceConfig(
            signal_indexes,
            duration_s=60.0,
            sample_interval_s=0.1,
            resolve_names=False,
        ),
        inbox=inbox,
        cancel=token,
    )
    try:
        if interactive_matplotlib_available():
            import matplotlib.pyplot as plt

            view = MatplotlibTraceView(run, inbox, ("Z", "Current"))
            with cancel_on_sigint(token):
                view.start()
                plt.show(block=True)
                result = run.result()
        else:
            with cancel_on_sigint(token):
                run.start()
                monitor_blocking(run, inbox)
                result = run.result()
        print(run.state.value, result.n_samples, "samples")
    finally:
        # A timeout from result() means this close must be deferred until done.
        if run.state is not RunState.RUNNING:
            client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MatplotlibTraceView",
    "interactive_matplotlib_available",
    "monitor_blocking",
]
