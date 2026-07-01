"""Pure, opt-in background transforms for already-read image arrays."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import cast

import numpy as np

from ..types import NaNPolicy

logger = logging.getLogger(__name__)


def subtract_average(
    array: np.ndarray, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> np.ndarray:
    return _subtract_means(array, axis=1, nan_policy=nan_policy)


def subtract_vaverage(
    array: np.ndarray, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> np.ndarray:
    return _subtract_means(array, axis=0, nan_policy=nan_policy)


def subtract_line(
    array: np.ndarray, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> np.ndarray:
    return _subtract_fits(array, vertical=False, nan_policy=nan_policy)


def subtract_vline(
    array: np.ndarray, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> np.ndarray:
    return _subtract_fits(array, vertical=True, nan_policy=nan_policy)


def subtract_plane(
    array: np.ndarray, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> np.ndarray:
    values = _prepare(array, nan_policy)
    finite = np.isfinite(values)
    if not finite.any():
        return values
    yy, xx = np.indices(values.shape, dtype=float)
    design = np.column_stack((xx[finite], yy[finite], np.ones(int(finite.sum()))))
    coefficients, *_ = np.linalg.lstsq(design, values[finite], rcond=None)
    plane = coefficients[0] * xx + coefficients[1] * yy + coefficients[2]
    values[finite] -= plane[finite]
    return cast(np.ndarray, values)


TRANSFORMS: dict[str, Callable[..., np.ndarray]] = {
    "subtract_average": subtract_average,
    "subtract_vaverage": subtract_vaverage,
    "subtract_line": subtract_line,
    "subtract_vline": subtract_vline,
    "subtract_plane": subtract_plane,
}


def apply_transform(
    array: np.ndarray,
    name: str,
    *,
    nan_policy: NaNPolicy = NaNPolicy.WARN,
) -> np.ndarray:
    try:
        transform = TRANSFORMS[name]
    except KeyError as exc:
        raise ValueError(f"unknown transform {name!r}") from exc
    return transform(array, nan_policy=nan_policy)


def _subtract_means(
    array: np.ndarray, *, axis: int, nan_policy: NaNPolicy
) -> np.ndarray:
    values = _prepare(array, nan_policy)
    finite = np.isfinite(values)
    for index in range(values.shape[0 if axis == 1 else 1]):
        selector = (index, slice(None)) if axis == 1 else (slice(None), index)
        selected = values[selector]
        mask = finite[selector]
        if mask.any():
            selected[mask] -= selected[mask].mean()
    return values


def _subtract_fits(
    array: np.ndarray, *, vertical: bool, nan_policy: NaNPolicy
) -> np.ndarray:
    values = _prepare(array, nan_policy)
    count = values.shape[1] if vertical else values.shape[0]
    for index in range(count):
        selector = (slice(None), index) if vertical else (index, slice(None))
        selected = values[selector]
        finite = np.isfinite(selected)
        x: np.ndarray = np.arange(selected.size, dtype=float)
        if finite.sum() >= 2:
            fit = np.polyfit(x[finite], selected[finite], 1)
            selected[finite] -= np.polyval(fit, x[finite])
        elif finite.any():
            selected[finite] -= selected[finite].mean()
    return cast(np.ndarray, values)


def _prepare(array: np.ndarray, policy: NaNPolicy) -> np.ndarray:
    values = np.array(array, dtype=np.float64, copy=True)
    if values.ndim != 2:
        raise ValueError(f"image transform requires a 2-D array, got {values.shape}")
    non_finite = int((~np.isfinite(values)).sum())
    if non_finite and policy is NaNPolicy.RAISE:
        raise ValueError(f"image contains {non_finite} non-finite values")
    if non_finite and policy is NaNPolicy.WARN:
        logger.warning(
            "Image contains %d non-finite values; fitting finite values only",
            non_finite,
        )
    return cast(np.ndarray, values)


__all__ = [
    "TRANSFORMS",
    "apply_transform",
    "subtract_average",
    "subtract_line",
    "subtract_plane",
    "subtract_vaverage",
    "subtract_vline",
]
