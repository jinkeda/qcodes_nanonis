"""Read-only, deadline-scheduled polling time traces."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from numbers import Integral
from typing import Any, cast

import numpy as np

from ...protocol import NanonisCommandError
from ...types import NaNPolicy
from ..cancellation import (
    CancelToken,
    ProgressCallback,
    ProgressEvent,
    report_progress,
)
from ..errors import NonFiniteTimeTraceDataError, TimeTraceResponseError
from ..protocols import CommandClient
from .models import TimeTraceConfig
from .result import FloatArray, TimeTraceResult, inspect_non_finite_trace

logger = logging.getLogger(__name__)
_WORKFLOW_NAME = "datalog.time_trace"


class TimeTraceWorkflow:
    def __init__(
        self,
        client: CommandClient,
        *,
        nan_policy: NaNPolicy = NaNPolicy.WARN,
    ) -> None:
        if not isinstance(nan_policy, NaNPolicy):
            raise TypeError("nan_policy must be a NaNPolicy")
        self.client = client
        self.nan_policy = nan_policy

    def run(
        self,
        config: TimeTraceConfig,
        *,
        cancel: CancelToken | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> TimeTraceResult:
        if not isinstance(config, TimeTraceConfig):
            raise TypeError("config must be a TimeTraceConfig")

        nanonis_version = self._read_nanonis_version()
        signal_names = self._resolve_names(config) if config.resolve_names else ()

        n_signals = len(config.signal_indexes)
        values: FloatArray = np.empty((n_signals, config.n_samples), dtype=np.float64)
        elapsed: FloatArray = np.empty(config.n_samples, dtype=np.float64)
        tolerance = 0.5 * config.sample_interval_s
        late = 0
        acquired = 0
        t0 = time.monotonic()
        started_at = datetime.now(timezone.utc)
        deadline = t0
        last_progress = t0
        was_cancelled = False

        for sample_index in range(config.n_samples):
            # This check is intentionally unconditional: a late loop does not
            # sleep, but still has to observe cancellation before the send.
            if cancel is not None and cancel.cancelled:
                was_cancelled = True
                break
            remaining = deadline - time.monotonic()
            if remaining > 0:
                if cancel is not None:
                    if cancel.wait(remaining):
                        was_cancelled = True
                        break
                else:
                    time.sleep(remaining)

            acquisition_started = time.monotonic()
            lateness = acquisition_started - deadline
            if sample_index > 0 and lateness > tolerance:
                late += 1
                # A counted overrun rebases the next tick. This avoids a burst
                # of catch-up reads while ordinary wakeup jitter stays on-grid.
                deadline = acquisition_started + config.sample_interval_s
            else:
                deadline += config.sample_interval_s

            response = self.client.send(
                "Signals.ValsGet",
                n_signals,
                config.signal_indexes,
                1 if config.wait_for_newest_data else 0,
            )
            row = _extract_values(response, expected=n_signals)
            sample_elapsed = time.monotonic() - t0
            if acquired and sample_elapsed <= elapsed[acquired - 1]:
                # Some supported Python/Windows builds expose a coarse
                # ``monotonic`` clock. Preserve ordering at that clock's
                # indistinguishable ticks with the smallest float64 increment.
                sample_elapsed = np.nextafter(elapsed[acquired - 1], np.inf)
            elapsed[acquired] = sample_elapsed
            values[:, acquired] = row
            acquired += 1

            now = time.monotonic()
            if now - last_progress >= 1.0:
                report_progress(
                    on_progress,
                    ProgressEvent(
                        workflow=_WORKFLOW_NAME,
                        fraction=acquired / config.n_samples,
                        message=f"acquired {acquired}/{config.n_samples} samples",
                        elapsed_s=now - t0,
                    ),
                )
                last_progress = now

        finished_at = datetime.now(timezone.utc)
        result = TimeTraceResult(
            signal_indexes=config.signal_indexes,
            signal_names=signal_names,
            elapsed_s=elapsed[:acquired],
            values=values[:, :acquired],
            requested_interval_s=config.sample_interval_s,
            started_at=started_at,
            finished_at=finished_at,
            late_sample_count=late,
            cancelled=was_cancelled,
            nanonis_version=nanonis_version,
            requested_duration_s=config.duration_s,
            wait_for_newest_data=config.wait_for_newest_data,
            resolve_names=config.resolve_names,
        )
        result = _apply_nan_policy(result, self.nan_policy)
        report_progress(
            on_progress,
            ProgressEvent(
                workflow=_WORKFLOW_NAME,
                fraction=acquired / config.n_samples,
                message=("cancelled" if was_cancelled else "complete"),
                elapsed_s=max(0.0, time.monotonic() - t0),
            ),
        )
        return result

    def _read_nanonis_version(self) -> str | None:
        try:
            response = self.client.send("Util.VersionGet")
        except NanonisCommandError:
            return None
        if isinstance(response, str):
            return response
        mapping = _response_mapping(response, "Util.VersionGet")
        if "version" not in mapping:
            raise TimeTraceResponseError("Util.VersionGet missing 'version'")
        return str(mapping["version"])

    def _resolve_names(self, config: TimeTraceConfig) -> tuple[str, ...]:
        response = _response_mapping(
            self.client.send("Signals.NamesGet"), "Signals.NamesGet"
        )
        if "signals_names_number" not in response:
            raise TimeTraceResponseError(
                "Signals.NamesGet missing 'signals_names_number'"
            )
        if "signals_names" not in response:
            raise TimeTraceResponseError("Signals.NamesGet missing 'signals_names'")
        count = response["signals_names_number"]
        if not _is_integer(count):
            raise TimeTraceResponseError(
                "Signals.NamesGet signals_names_number must be an integer"
            )
        names = _one_dimensional_sequence(
            response["signals_names"], "Signals.NamesGet signals_names"
        )
        if int(count) != len(names):
            raise TimeTraceResponseError(
                "Signals.NamesGet declared name count does not match array length"
            )
        if any(index >= int(count) for index in config.signal_indexes):
            raise TimeTraceResponseError(
                "Signals.NamesGet does not contain every requested signal index"
            )
        return tuple(str(names[index]) for index in config.signal_indexes)


def _extract_values(response: Any, *, expected: int) -> FloatArray:
    mapping = _response_mapping(response, "Signals.ValsGet")
    if "signals_values_size" not in mapping:
        raise TimeTraceResponseError("Signals.ValsGet missing 'signals_values_size'")
    if "signals_values" not in mapping:
        raise TimeTraceResponseError("Signals.ValsGet missing 'signals_values'")
    declared = mapping["signals_values_size"]
    if not _is_integer(declared):
        raise TimeTraceResponseError(
            "Signals.ValsGet signals_values_size must be an integer"
        )
    try:
        values = np.asarray(mapping["signals_values"], dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise TimeTraceResponseError(
            "Signals.ValsGet signals_values must be numeric"
        ) from exc
    if values.ndim != 1:
        raise TimeTraceResponseError(
            "Signals.ValsGet signals_values must be one-dimensional"
        )
    if int(declared) != values.size:
        raise TimeTraceResponseError(
            "Signals.ValsGet declared value count does not match array length"
        )
    if values.size != expected:
        raise TimeTraceResponseError(
            f"Signals.ValsGet returned {values.size} values; expected {expected}"
        )
    return cast(FloatArray, values)


def _response_mapping(response: Any, command: str) -> Mapping[str, Any]:
    if not isinstance(response, Mapping):
        raise TimeTraceResponseError(f"{command} must return a mapping")
    return response


def _one_dimensional_sequence(value: Any, field: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        if not isinstance(value, np.ndarray):
            raise TimeTraceResponseError(f"{field} must be a one-dimensional array")
    array = np.asarray(value, dtype=object)
    if array.ndim != 1:
        raise TimeTraceResponseError(f"{field} must be a one-dimensional array")
    return tuple(array.tolist())


def _is_integer(value: Any) -> bool:
    return isinstance(value, Integral) and not isinstance(value, bool)


def _apply_nan_policy(result: TimeTraceResult, policy: NaNPolicy) -> TimeTraceResult:
    diagnostics = inspect_non_finite_trace(result)
    if not diagnostics.has_non_finite or policy is NaNPolicy.ALLOW:
        return result
    if policy is NaNPolicy.RAISE:
        raise NonFiniteTimeTraceDataError(result, diagnostics)
    logger.warning(
        "Time-trace data contains %d NaN and %d infinite values; "
        "affected signal indexes: %s",
        diagnostics.nan_count,
        diagnostics.inf_count,
        diagnostics.affected_signal_indexes,
    )
    return result


__all__ = ["TimeTraceWorkflow"]
