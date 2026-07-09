"""Immutable time-trace results and non-finite-data inspection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

from ...provenance import software_provenance

FloatArray: TypeAlias = npt.NDArray[np.float64]


@dataclass(frozen=True)
class TimeTraceNonFiniteDiagnostics:
    nan_count: int
    inf_count: int
    affected_signal_indexes: tuple[int, ...]
    affected_signal_names: tuple[str, ...]

    @property
    def has_non_finite(self) -> bool:
        return self.nan_count > 0 or self.inf_count > 0


@dataclass(frozen=True)
class TimeTraceResult:
    signal_indexes: tuple[int, ...]
    signal_names: tuple[str, ...]
    elapsed_s: FloatArray
    values: FloatArray
    requested_interval_s: float
    started_at: datetime
    finished_at: datetime
    late_sample_count: int
    cancelled: bool
    nanonis_version: str | None
    requested_duration_s: float | None = None
    wait_for_newest_data: bool | None = None
    resolve_names: bool | None = None

    def __post_init__(self) -> None:
        indexes = tuple(self.signal_indexes)
        names = tuple(self.signal_names)
        elapsed = np.array(self.elapsed_s, dtype=np.float64, copy=True)
        values = np.array(self.values, dtype=np.float64, copy=True)
        if not indexes or len(set(indexes)) != len(indexes):
            raise ValueError("signal_indexes must be non-empty and unique")
        if names and len(names) != len(indexes):
            raise ValueError("signal_names must be empty or match signal_indexes")
        if elapsed.ndim != 1:
            raise ValueError("elapsed_s must be one-dimensional")
        if values.shape != (len(indexes), elapsed.size):
            raise ValueError(
                "values shape must be (len(signal_indexes), len(elapsed_s))"
            )
        if elapsed.size > 1 and not bool(np.all(np.diff(elapsed) > 0)):
            raise ValueError("elapsed_s must be strictly increasing")
        if elapsed.size and (not bool(np.all(np.isfinite(elapsed))) or elapsed[0] < 0):
            raise ValueError("elapsed_s must be finite and non-negative")
        if not isfinite(self.requested_interval_s) or self.requested_interval_s <= 0:
            raise ValueError("requested_interval_s must be finite and > 0")
        if self.requested_duration_s is not None and (
            not isfinite(self.requested_duration_s)
            or self.requested_duration_s < self.requested_interval_s
        ):
            raise ValueError(
                "requested_duration_s must be finite and >= requested_interval_s"
            )
        for field, option_value in (
            ("wait_for_newest_data", self.wait_for_newest_data),
            ("resolve_names", self.resolve_names),
        ):
            if option_value is not None and not isinstance(option_value, bool):
                raise TypeError(f"{field} must be bool or None")
        for timestamp in (self.started_at, self.finished_at):
            offset = timestamp.utcoffset()
            if (
                timestamp.tzinfo is None
                or offset is None
                or offset.total_seconds() != 0
            ):
                raise ValueError("time-trace timestamps must be timezone-aware UTC")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at precedes started_at")
        if (
            not isinstance(self.late_sample_count, int)
            or isinstance(self.late_sample_count, bool)
            or self.late_sample_count < 0
            or self.late_sample_count > max(0, elapsed.size - 1)
        ):
            raise ValueError("late_sample_count is inconsistent with sample count")
        if not isinstance(self.cancelled, bool):
            raise TypeError("cancelled must be bool")
        if self.nanonis_version is not None and not isinstance(
            self.nanonis_version, str
        ):
            raise TypeError("nanonis_version must be str or None")
        elapsed.setflags(write=False)
        values.setflags(write=False)
        object.__setattr__(self, "signal_indexes", indexes)
        object.__setattr__(self, "signal_names", names)
        object.__setattr__(self, "elapsed_s", elapsed)
        object.__setattr__(self, "values", values)

    @property
    def n_samples(self) -> int:
        return int(self.elapsed_s.size)

    def signal_by_index(self, index: int) -> FloatArray:
        try:
            position = self.signal_indexes.index(index)
        except ValueError as exc:
            raise KeyError(f"signal index {index} was not recorded") from exc
        return self.values[position]

    def signal_by_name(self, name: str) -> FloatArray:
        if not self.signal_names:
            raise ValueError("signal names were not resolved")
        matches = tuple(
            index
            for index, resolved in zip(self.signal_indexes, self.signal_names)
            if resolved == name
        )
        if not matches:
            raise ValueError(f"signal name {name!r} was not recorded")
        if len(matches) > 1:
            raise ValueError(
                f"signal name {name!r} matches indexes {matches}; use signal_by_index"
            )
        return self.signal_by_index(matches[0])

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-compatible acquisition metadata (bulk arrays excluded)."""
        actual_span = float(self.elapsed_s[-1]) if self.elapsed_s.size else 0.0
        return {
            "format": "nanonis-time-trace",
            "software": software_provenance(),
            "controller": {"nanonis_version": self.nanonis_version},
            "signal_indexes": list(self.signal_indexes),
            "signal_names": list(self.signal_names),
            "n_samples": self.n_samples,
            "requested_interval_s": self.requested_interval_s,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "actual_span_s": actual_span,
            "late_sample_count": self.late_sample_count,
            "cancelled": self.cancelled,
            "config": {
                "signal_indexes": list(self.signal_indexes),
                "duration_s": self.requested_duration_s,
                "sample_interval_s": self.requested_interval_s,
                "wait_for_newest_data": self.wait_for_newest_data,
                "resolve_names": self.resolve_names,
            },
        }


def inspect_non_finite_trace(
    result: TimeTraceResult,
) -> TimeTraceNonFiniteDiagnostics:
    nan_mask = np.isnan(result.values)
    inf_mask = np.isinf(result.values)
    affected = np.any(nan_mask | inf_mask, axis=1)
    indexes = tuple(
        index for index, selected in zip(result.signal_indexes, affected) if selected
    )
    names = (
        tuple(name for name, selected in zip(result.signal_names, affected) if selected)
        if result.signal_names
        else ()
    )
    return TimeTraceNonFiniteDiagnostics(
        nan_count=int(nan_mask.sum()),
        inf_count=int(inf_mask.sum()),
        affected_signal_indexes=indexes,
        affected_signal_names=names,
    )


__all__ = [
    "FloatArray",
    "TimeTraceNonFiniteDiagnostics",
    "TimeTraceResult",
    "inspect_non_finite_trace",
]
