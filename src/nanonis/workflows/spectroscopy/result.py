"""Lossless normalization of BiasSpectr.Start responses."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from typing import Any, Mapping, TypeAlias

import numpy as np
import numpy.typing as npt

from ..errors import (
    NonFiniteSpectroscopyDataError,
    SpectroscopyResponseError,
)
from ..models import BiasSpectroscopyConfig, BiasSpectroscopySettings, SweepAxis

logger = logging.getLogger(__name__)
FloatArray: TypeAlias = npt.NDArray[np.float64]


class NaNPolicy(Enum):
    ALLOW = "allow"
    WARN = "warn"
    RAISE = "raise"


@dataclass(frozen=True)
class SpectroscopyTrace:
    name: str
    occurrence: int
    values: FloatArray

    @property
    def unique_name(self) -> str:
        return self.name if self.occurrence == 0 else f"{self.name}#{self.occurrence + 1}"


@dataclass(frozen=True)
class SpectroscopyParameter:
    name: str | None
    value: float


@dataclass(frozen=True)
class NonFiniteDiagnostics:
    nan_count: int
    inf_count: int
    fully_nan_channels: tuple[str, ...]
    affected_channels: tuple[str, ...]

    @property
    def has_non_finite(self) -> bool:
        return self.nan_count > 0 or self.inf_count > 0


@dataclass(frozen=True)
class BiasSpectroscopyResult:
    channel_names: tuple[str, ...]
    data: FloatArray
    data_rows: int
    data_columns: int
    parameters: tuple[SpectroscopyParameter, ...]
    requested_config: BiasSpectroscopyConfig
    effective_settings: BiasSpectroscopySettings
    acquisition_started_at: datetime
    acquisition_finished_at: datetime
    acquisition_duration: float
    estimated_acquisition_duration: float
    acquisition_timeout_used: float
    save_base_name: str = ""
    saved_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        data = np.array(self.data, dtype=np.float64, copy=True)
        data.setflags(write=False)
        object.__setattr__(self, "data", data)
        object.__setattr__(self, "channel_names", tuple(self.channel_names))
        object.__setattr__(self, "parameters", tuple(self.parameters))
        object.__setattr__(self, "saved_paths", tuple(self.saved_paths))
        if data.shape != (self.data_rows, self.data_columns):
            raise ValueError("matrix shape != declared (rows, columns)")
        if len(self.channel_names) != self.data_rows:
            raise ValueError("channel-name count != data rows (orientation)")
        for value in (self.acquisition_started_at, self.acquisition_finished_at):
            offset = value.utcoffset()
            if value.tzinfo is None or offset is None:
                raise ValueError("acquisition timestamps must be timezone-aware")
            if offset.total_seconds() != 0:
                raise ValueError("acquisition timestamps must be UTC")
        if self.acquisition_duration < 0 or not isfinite(self.acquisition_duration):
            raise ValueError("acquisition_duration must be finite and non-negative")
        if self.acquisition_finished_at < self.acquisition_started_at:
            raise ValueError("finish precedes start")
        if (
            not isfinite(self.estimated_acquisition_duration)
            or self.estimated_acquisition_duration < 0
        ):
            raise ValueError("estimated acquisition duration must be finite and >= 0")
        if not isfinite(self.acquisition_timeout_used) or self.acquisition_timeout_used <= 0:
            raise ValueError("acquisition timeout used must be finite and > 0")

    @property
    def points_match_request(self) -> bool:
        return self.data_columns == self.effective_settings.points

    def traces(self) -> tuple[SpectroscopyTrace, ...]:
        seen: dict[str, int] = {}
        traces = []
        for index, name in enumerate(self.channel_names):
            values: FloatArray = self.data[index]
            occurrence = seen.get(name, 0)
            seen[name] = occurrence + 1
            traces.append(SpectroscopyTrace(name, occurrence, values))
        return tuple(traces)

    def forward_axis(self) -> SweepAxis:
        start, stop = self.effective_settings.limits
        return SweepAxis(
            np.linspace(start, stop, self.effective_settings.points),
            direction="forward",
        )

    def backward_axis(self) -> SweepAxis:
        forward = self.forward_axis().values
        return SweepAxis(forward[::-1], direction="backward")


def normalize_bias_spectroscopy_response(
    response: Mapping[str, Any],
    *,
    config: BiasSpectroscopyConfig,
    effective: BiasSpectroscopySettings,
    acquisition_started_at: datetime,
    acquisition_finished_at: datetime,
    acquisition_duration: float,
    estimated_acquisition_duration: float,
    acquisition_timeout_used: float,
    nan_policy: NaNPolicy = NaNPolicy.WARN,
) -> BiasSpectroscopyResult:
    try:
        names = tuple(str(value) for value in response["channels_names"])
        rows = int(response["data_rows"])
        columns = int(response["data_columns"])
        data = response["data"]
        declared_channels = int(response["num_channels"])
        declared_parameters = int(response["num_parameters"])
        parameter_values = tuple(float(value) for value in response["parameters"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SpectroscopyResponseError(f"invalid BiasSpectr.Start response: {exc}") from exc

    if np.shape(data) != (rows, columns):
        raise SpectroscopyResponseError(
            f"shape {np.shape(data)} != declared ({rows}, {columns})"
        )
    if declared_channels != len(names):
        raise SpectroscopyResponseError("declared channel count != names")
    if len(names) != rows:
        raise SpectroscopyResponseError("cannot map data rows to channel names")
    if declared_parameters != len(parameter_values):
        raise SpectroscopyResponseError("declared parameter count != values")

    ordered_parameter_names = (
        effective.fixed_parameter_names + effective.parameter_names
    )
    parameters = tuple(
        SpectroscopyParameter(
            ordered_parameter_names[index]
            if index < len(ordered_parameter_names)
            else None,
            value,
        )
        for index, value in enumerate(parameter_values)
    )
    if columns != effective.points:
        logger.warning(
            "BiasSpectr.Start returned %d columns for %d effective points; "
            "the raw result is preserved",
            columns,
            effective.points,
        )

    result = BiasSpectroscopyResult(
        channel_names=names,
        data=data,
        data_rows=rows,
        data_columns=columns,
        parameters=parameters,
        requested_config=config,
        effective_settings=effective,
        acquisition_started_at=acquisition_started_at,
        acquisition_finished_at=acquisition_finished_at,
        acquisition_duration=acquisition_duration,
        estimated_acquisition_duration=estimated_acquisition_duration,
        acquisition_timeout_used=acquisition_timeout_used,
        save_base_name=config.save_base_name,
    )
    return apply_nan_policy(result, nan_policy)


def inspect_non_finite_data(result: BiasSpectroscopyResult) -> NonFiniteDiagnostics:
    nan_mask = np.isnan(result.data)
    inf_mask = np.isinf(result.data)
    affected = np.any(nan_mask | inf_mask, axis=1)
    fully_nan = np.all(nan_mask, axis=1)
    traces = result.traces()
    return NonFiniteDiagnostics(
        nan_count=int(nan_mask.sum()),
        inf_count=int(inf_mask.sum()),
        fully_nan_channels=tuple(
            trace.unique_name for trace, selected in zip(traces, fully_nan) if selected
        ),
        affected_channels=tuple(
            trace.unique_name for trace, selected in zip(traces, affected) if selected
        ),
    )


def apply_nan_policy(
    result: BiasSpectroscopyResult, policy: NaNPolicy
) -> BiasSpectroscopyResult:
    diagnostics = inspect_non_finite_data(result)
    if not diagnostics.has_non_finite or policy is NaNPolicy.ALLOW:
        return result
    if policy is NaNPolicy.RAISE:
        raise NonFiniteSpectroscopyDataError(result, diagnostics)
    logger.warning(
        "Spectroscopy data contains %d NaN and %d infinite values; "
        "affected channels: %s",
        diagnostics.nan_count,
        diagnostics.inf_count,
        ", ".join(diagnostics.affected_channels),
    )
    return result
