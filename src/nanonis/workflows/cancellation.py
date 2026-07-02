"""Thread-safe cooperative cancellation and workflow progress reporting."""

from __future__ import annotations

import logging
import signal
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Event
from types import FrameType
from typing import Callable, Iterator

from .errors import WorkflowCancelledError

logger = logging.getLogger(__name__)


class CancelToken:
    """Thread-safe cooperative cancellation flag."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise WorkflowCancelledError("workflow cancelled")

    def wait(self, timeout: float) -> bool:
        """Wait for cancellation for at most ``timeout`` seconds."""
        return self._event.wait(timeout)


@dataclass(frozen=True)
class ProgressEvent:
    workflow: str
    fraction: float | None
    message: str
    elapsed_s: float

    def __post_init__(self) -> None:
        if self.fraction is not None and not 0.0 <= self.fraction <= 1.0:
            raise ValueError("progress fraction must be between 0 and 1")
        if self.elapsed_s < 0:
            raise ValueError("progress elapsed_s must be non-negative")


ProgressCallback = Callable[[ProgressEvent], None]


@dataclass(frozen=True)
class SampleEvent:
    """One stored sample emitted by a time-trace workflow."""

    workflow: str
    sample_index: int
    elapsed_s: float
    values: tuple[float, ...]


SampleCallback = Callable[[SampleEvent], None]


def report_progress(callback: ProgressCallback | None, event: ProgressEvent) -> None:
    """Invoke a progress callback without letting it abort acquisition."""
    if callback is None:
        return
    try:
        callback(event)
    except Exception:
        logger.exception("progress callback failed for %s", event.workflow)


@contextmanager
def cancel_on_sigint(token: CancelToken) -> Iterator[CancelToken]:
    """Cancel on first SIGINT; let a second SIGINT raise ``KeyboardInterrupt``.

    ``signal.signal`` requires the main thread. The context manager intentionally
    leaves that restriction visible instead of pretending signal installation is
    available from worker threads.
    """

    previous = signal.getsignal(signal.SIGINT)
    interrupted = False

    def handler(signum: int, frame: FrameType | None) -> None:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            token.cancel()
            return
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.default_int_handler(signum, frame)

    signal.signal(signal.SIGINT, handler)
    try:
        yield token
    finally:
        signal.signal(signal.SIGINT, previous)


__all__ = [
    "CancelToken",
    "ProgressCallback",
    "ProgressEvent",
    "SampleCallback",
    "SampleEvent",
    "cancel_on_sigint",
    "report_progress",
]
