"""Validated configuration for polling time traces."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite
from numbers import Integral, Real

MAX_TRACE_ELEMENTS = 10_000_000


@dataclass(frozen=True)
class TimeTraceConfig:
    """A fixed-count, deadline-scheduled Signals polling request.

    The element cap limits final float64 value storage to about 80 MB. Peak
    transient use is about twice that because ``TimeTraceResult`` defensively
    copies the workflow buffers before exposing immutable arrays.
    """

    signal_indexes: tuple[int, ...]
    duration_s: float
    sample_interval_s: float = 0.1
    wait_for_newest_data: bool = True
    resolve_names: bool = True

    def __post_init__(self) -> None:
        try:
            indexes = tuple(self.signal_indexes)
        except TypeError as exc:
            raise ValueError("signal_indexes must be an iterable of integers") from exc
        object.__setattr__(self, "signal_indexes", indexes)
        if not indexes:
            raise ValueError("signal_indexes must not be empty")
        if any(
            not isinstance(index, Integral) or isinstance(index, bool)
            for index in indexes
        ):
            raise ValueError("signal indexes must be integers")
        normalized = tuple(int(index) for index in indexes)
        object.__setattr__(self, "signal_indexes", normalized)
        if len(set(normalized)) != len(normalized):
            raise ValueError("signal indexes must be unique")
        if any(index < 0 or index > 127 for index in normalized):
            raise ValueError("signal indexes must be in [0, 127]")
        if not isinstance(self.duration_s, Real) or isinstance(self.duration_s, bool):
            raise ValueError("duration_s must be a real number")
        if not isinstance(self.sample_interval_s, Real) or isinstance(
            self.sample_interval_s, bool
        ):
            raise ValueError("sample_interval_s must be a real number")
        duration = float(self.duration_s)
        interval = float(self.sample_interval_s)
        object.__setattr__(self, "duration_s", duration)
        object.__setattr__(self, "sample_interval_s", interval)
        if not isfinite(duration) or duration <= 0:
            raise ValueError("duration_s must be finite and > 0")
        if not isfinite(interval) or interval <= 0:
            raise ValueError("sample_interval_s must be finite and > 0")
        if duration < interval:
            raise ValueError("duration_s must be >= sample_interval_s")
        if not isinstance(self.wait_for_newest_data, bool):
            raise TypeError("wait_for_newest_data must be bool")
        if not isinstance(self.resolve_names, bool):
            raise TypeError("resolve_names must be bool")
        if self.n_samples * len(normalized) > MAX_TRACE_ELEMENTS:
            raise ValueError(f"trace exceeds MAX_TRACE_ELEMENTS ({MAX_TRACE_ELEMENTS})")

    @property
    def n_samples(self) -> int:
        return floor(self.duration_s / self.sample_interval_s + 1e-9) + 1


__all__ = ["MAX_TRACE_ELEMENTS", "TimeTraceConfig"]
