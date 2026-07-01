"""I/O-free non-finite validation for data-reader domain models."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from ..types import NaNPolicy
from .models import DatData, Grid3DData, SxmData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NonFiniteData:
    nan_count: int
    inf_count: int
    affected: tuple[str, ...]

    @property
    def has_non_finite(self) -> bool:
        return bool(self.nan_count or self.inf_count)


class NonFiniteFileDataError(ValueError):
    def __init__(self, diagnostics: NonFiniteData):
        self.diagnostics = diagnostics
        super().__init__(
            f"file data contains {diagnostics.nan_count} NaN and "
            f"{diagnostics.inf_count} infinite values"
        )


def inspect_non_finite(data: SxmData | Grid3DData | DatData) -> NonFiniteData:
    arrays: list[tuple[str, np.ndarray]] = []
    if isinstance(data, SxmData):
        for channel in data.channels:
            arrays.extend(
                (f"{channel.name}[{direction}]", channel.data(direction))
                for direction in channel.directions
            )
    elif isinstance(data, Grid3DData):
        arrays.extend((channel.name, channel.values) for channel in data.channels)
        arrays.extend(data.fixed_parameters.items())
        arrays.append((data.sweep_signal.name, data.sweep_signal.values))
    else:
        arrays.extend((column.name, column.values) for column in data.columns)
    return _inspect_arrays(arrays)


def apply_nan_policy(
    data: SxmData | Grid3DData | DatData,
    policy: NaNPolicy,
) -> SxmData | Grid3DData | DatData:
    diagnostics = inspect_non_finite(data)
    if not diagnostics.has_non_finite or policy is NaNPolicy.ALLOW:
        return data
    if policy is NaNPolicy.RAISE:
        raise NonFiniteFileDataError(diagnostics)
    logger.warning(
        "File data contains %d NaN and %d infinite values; affected: %s",
        diagnostics.nan_count,
        diagnostics.inf_count,
        ", ".join(diagnostics.affected),
    )
    return data


def _inspect_arrays(arrays: Iterable[tuple[str, np.ndarray]]) -> NonFiniteData:
    nan_count = inf_count = 0
    affected: list[str] = []
    for name, values in arrays:
        nans = int(np.isnan(values).sum())
        infs = int(np.isinf(values).sum())
        nan_count += nans
        inf_count += infs
        if nans or infs:
            affected.append(name)
    return NonFiniteData(nan_count, inf_count, tuple(affected))


__all__ = [
    "NonFiniteData",
    "NonFiniteFileDataError",
    "apply_nan_policy",
    "inspect_non_finite",
]
