"""Matplotlib-free live-view hand-off, history, and worker lifecycle."""

from __future__ import annotations

import math
import threading
from collections import deque
from enum import Enum

import numpy as np

from ..cancellation import (
    CancelToken,
    ProgressCallback,
    SampleEvent,
)
from ..errors import LiveViewTimeoutError
from .models import TimeTraceConfig
from .result import FloatArray, TimeTraceResult
from .workflow import TimeTraceWorkflow


class SampleInbox:
    """Thread-safe, bounded producer-to-UI sample hand-off."""

    def __init__(self, maxlen: int) -> None:
        if not isinstance(maxlen, int) or isinstance(maxlen, bool) or maxlen <= 0:
            raise ValueError("maxlen must be a positive integer")
        self._maxlen = maxlen
        self._events: deque[SampleEvent] = deque()
        self._dropped_count = 0
        self._lock = threading.Lock()

    def push(self, event: SampleEvent) -> None:
        """Append one event, dropping the oldest queued event when full."""
        if not isinstance(event, SampleEvent):
            raise TypeError("event must be a SampleEvent")
        with self._lock:
            if len(self._events) == self._maxlen:
                self._events.popleft()
                self._dropped_count += 1
            self._events.append(event)

    def drain(self) -> list[SampleEvent]:
        """Atomically remove and return every currently queued event."""
        with self._lock:
            events = list(self._events)
            self._events.clear()
        return events

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count


class TraceHistory:
    """UI-owned rolling history with gap-preserving display decimation."""

    def __init__(
        self,
        n_signals: int,
        *,
        window_s: float | None = 60.0,
        max_history_samples: int = 100_000,
        max_points: int = 2000,
    ) -> None:
        if (
            not isinstance(n_signals, int)
            or isinstance(n_signals, bool)
            or n_signals <= 0
        ):
            raise ValueError("n_signals must be a positive integer")
        if window_s is not None and (
            not isinstance(window_s, (int, float))
            or isinstance(window_s, bool)
            or not math.isfinite(window_s)
            or window_s <= 0
        ):
            raise ValueError("window_s must be finite and positive or None")
        for name, value in (
            ("max_history_samples", max_history_samples),
            ("max_points", max_points),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

        self.n_signals = n_signals
        self.window_s = float(window_s) if window_s is not None else None
        self.max_history_samples = max_history_samples
        self.max_points = max_points
        self._elapsed: list[float] = []
        self._values: list[tuple[float, ...]] = []
        self._last_sample_index: int | None = None
        self._last_sample_elapsed: float | None = None

    def extend(self, events: list[SampleEvent]) -> None:
        """Append ordered events and mark missing acquisition indexes with NaNs."""
        for event in events:
            if not isinstance(event, SampleEvent):
                raise TypeError("events must contain SampleEvent instances")
            if len(event.values) != self.n_signals:
                raise ValueError(
                    f"event has {len(event.values)} values; expected {self.n_signals}"
                )
            if self._last_sample_index is not None:
                if event.sample_index <= self._last_sample_index:
                    raise ValueError("sample indexes must be strictly increasing")
                if (
                    self._last_sample_elapsed is not None
                    and event.elapsed_s <= self._last_sample_elapsed
                ):
                    raise ValueError("sample elapsed times must be strictly increasing")

            expected = (
                0
                if self._last_sample_index is None
                else self._last_sample_index + 1
            )
            if event.sample_index != expected:
                self._append_gap(event.elapsed_s)

            self._elapsed.append(float(event.elapsed_s))
            self._values.append(tuple(float(value) for value in event.values))
            self._last_sample_index = event.sample_index
            self._last_sample_elapsed = float(event.elapsed_s)

        self._trim_history()

    def display_arrays(self) -> tuple[FloatArray, FloatArray]:
        """Return elapsed and ``(signals, points)`` arrays for plotting.

        Every row containing a non-finite value and the newest row are retained.
        If those mandatory rows alone exceed ``max_points``, preserving gaps takes
        precedence and the returned arrays necessarily exceed that soft limit.
        """
        if not self._elapsed:
            return (
                np.empty(0, dtype=np.float64),
                np.empty((self.n_signals, 0), dtype=np.float64),
            )

        elapsed = np.asarray(self._elapsed, dtype=np.float64)
        rows = np.asarray(self._values, dtype=np.float64)
        if elapsed.size <= self.max_points:
            return elapsed.copy(), rows.T.copy()

        non_finite = ~np.all(np.isfinite(rows), axis=1)
        mandatory = np.flatnonzero(non_finite).tolist()
        final_index = elapsed.size - 1
        if final_index not in mandatory:
            mandatory.append(final_index)
        mandatory_set = set(mandatory)

        budget = self.max_points - len(mandatory_set)
        if budget > 0:
            candidates = np.asarray(
                [index for index in range(elapsed.size) if index not in mandatory_set],
                dtype=np.int64,
            )
            if candidates.size <= budget:
                selected = candidates.tolist()
            else:
                positions = np.linspace(
                    0, candidates.size - 1, num=budget, dtype=np.int64
                )
                selected = candidates[positions].tolist()
        else:
            selected = []

        indexes = np.asarray(
            sorted(mandatory_set.union(selected)), dtype=np.int64
        )
        return elapsed[indexes].copy(), rows[indexes].T.copy()

    def _append_gap(self, next_elapsed: float) -> None:
        if self._last_sample_elapsed is None:
            gap_elapsed = float(next_elapsed)
        else:
            gap_elapsed = self._last_sample_elapsed + (
                float(next_elapsed) - self._last_sample_elapsed
            ) / 2.0
        self._elapsed.append(gap_elapsed)
        self._values.append((float("nan"),) * self.n_signals)

    def _trim_history(self) -> None:
        start = max(0, len(self._elapsed) - self.max_history_samples)
        if self.window_s is not None and self._last_sample_elapsed is not None:
            cutoff = self._last_sample_elapsed - self.window_s
            start = max(start, int(np.searchsorted(self._elapsed, cutoff, side="left")))
        if start:
            del self._elapsed[:start]
            del self._values[:start]


class RunState(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTraceRun:
    """Single-use, non-daemon background wrapper for a time-trace workflow."""

    def __init__(
        self,
        workflow: TimeTraceWorkflow,
        config: TimeTraceConfig,
        *,
        inbox: SampleInbox,
        cancel: CancelToken | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        if not isinstance(workflow, TimeTraceWorkflow):
            raise TypeError("workflow must be a TimeTraceWorkflow")
        if not isinstance(config, TimeTraceConfig):
            raise TypeError("config must be a TimeTraceConfig")
        if not isinstance(inbox, SampleInbox):
            raise TypeError("inbox must be a SampleInbox")
        self._workflow = workflow
        self._config = config
        self._inbox = inbox
        self._cancel = cancel if cancel is not None else CancelToken()
        self._on_progress = on_progress
        self._state = RunState.NOT_STARTED
        self._result: TimeTraceResult | None = None
        self._exception: BaseException | None = None
        self._done_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._run,
            name="nanonis-time-trace",
            daemon=False,
        )

    def start(self) -> None:
        """Start acquisition and return immediately."""
        with self._lock:
            if self._state is not RunState.NOT_STARTED:
                raise RuntimeError("background trace run is single-use")
            self._state = RunState.RUNNING
            self._thread.start()

    @property
    def state(self) -> RunState:
        with self._lock:
            return self._state

    @property
    def done(self) -> bool:
        return self._done_event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for any terminal state, returning false on timeout."""
        return self._done_event.wait(timeout)

    def cancel(self) -> None:
        self._cancel.cancel()

    def result(self, timeout: float | None = None) -> TimeTraceResult:
        """Join and return the result, or re-raise a worker failure."""
        with self._lock:
            if self._state is RunState.NOT_STARTED:
                raise RuntimeError("background trace run has not been started")
        if not self._done_event.wait(timeout):
            raise LiveViewTimeoutError(
                "background trace is still running and still owns the client; "
                "do not reuse or close the client until run.done is true"
            )
        self._thread.join()
        if self._exception is not None:
            raise self._exception
        if self._result is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("background trace ended without a result")
        return self._result

    def _run(self) -> None:
        try:
            result = self._workflow.run(
                self._config,
                cancel=self._cancel,
                on_progress=self._on_progress,
                on_sample=self._inbox.push,
            )
        except BaseException as exc:
            with self._lock:
                self._exception = exc
                self._state = RunState.FAILED
        else:
            with self._lock:
                self._result = result
                self._state = (
                    RunState.CANCELLED if result.cancelled else RunState.FINISHED
                )
        finally:
            self._done_event.set()


__all__ = [
    "BackgroundTraceRun",
    "RunState",
    "SampleInbox",
    "TraceHistory",
]
