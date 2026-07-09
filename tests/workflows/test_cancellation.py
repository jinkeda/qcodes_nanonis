from __future__ import annotations

import signal
import threading
import time

import pytest

from nanonis.workflows import (
    CancelToken,
    ProgressEvent,
    WorkflowCancelledError,
    cancel_on_sigint,
)
from nanonis.workflows.cancellation import report_progress


def test_token_starts_uncancelled_and_raises_after_cancel() -> None:
    token = CancelToken()
    assert not token.cancelled
    token.raise_if_cancelled()
    token.cancel()
    assert token.cancelled
    with pytest.raises(WorkflowCancelledError):
        token.raise_if_cancelled()


def test_wait_returns_early_on_cross_thread_cancel() -> None:
    token = CancelToken()
    thread = threading.Timer(0.02, token.cancel)
    thread.start()
    started = time.monotonic()
    try:
        assert token.wait(1.0)
    finally:
        thread.join()
    assert time.monotonic() - started < 0.5


def test_progress_callback_exception_is_suppressed(caplog) -> None:
    event = ProgressEvent("test", 0.5, "half", 1.0)

    def fail(_: ProgressEvent) -> None:
        raise RuntimeError("callback broke")

    report_progress(fail, event)
    assert "progress callback failed" in caplog.text


def test_cancel_on_sigint_cancels_then_restores(monkeypatch) -> None:
    installed: dict[int, object] = {signal.SIGINT: signal.SIG_IGN}

    monkeypatch.setattr(signal, "getsignal", lambda signum: installed[signum])
    monkeypatch.setattr(
        signal, "signal", lambda signum, handler: installed.__setitem__(signum, handler)
    )
    token = CancelToken()
    with cancel_on_sigint(token):
        handler = installed[signal.SIGINT]
        assert callable(handler)
        handler(signal.SIGINT, None)
        assert token.cancelled
    assert installed[signal.SIGINT] is signal.SIG_IGN
