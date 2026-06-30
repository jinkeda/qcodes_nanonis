"""Immutable, lossless scan result normalization."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Any, Iterable, Mapping, TypeAlias

import numpy as np
import numpy.typing as npt

from ..errors import NonFiniteScanDataError, ScanResponseError
from ..spectroscopy.result import NaNPolicy, NonFiniteDiagnostics
from .models import DataDirection, ScanConfig, ScanDirection, ScanFrame, ScanSettings

logger = logging.getLogger(__name__)
FloatArray: TypeAlias = npt.NDArray[np.float64]


@dataclass(frozen=True)
class ScanChannelImage:
    name: str
    channel_index: int
    direction: DataDirection
    data: FloatArray
    scan_direction: ScanDirection = "up"

    def __post_init__(self) -> None:
        data = np.array(self.data, dtype=np.float64, copy=True)
        if data.ndim != 2:
            raise ValueError("scan channel data must be two-dimensional")
        data.setflags(write=False)
        object.__setattr__(self, "data", data)
        if self.channel_index < 0:
            raise ValueError("channel_index must be non-negative")
        if self.direction not in ("forward", "backward"):
            raise ValueError("invalid data direction")
        if self.scan_direction not in ("up", "down"):
            raise ValueError("invalid scan direction")

    @property
    def rows(self) -> int:
        return int(self.data.shape[0])

    @property
    def columns(self) -> int:
        return int(self.data.shape[1])


@dataclass(frozen=True)
class ScanResult:
    images: tuple[ScanChannelImage, ...]
    frame: ScanFrame
    requested_config: ScanConfig
    effective_settings: ScanSettings
    saved_path: str
    acquisition_started_at: datetime
    acquisition_finished_at: datetime
    acquisition_duration: float
    estimated_acquisition_duration: float
    acquisition_timeout_used: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "images", tuple(self.images))
        if len({(image.channel_index, image.direction) for image in self.images}) != len(
            self.images
        ):
            raise ValueError("duplicate channel/direction scan image")
        if not isinstance(self.saved_path, str):
            raise TypeError("saved_path must be a string")
        for timestamp in (self.acquisition_started_at, self.acquisition_finished_at):
            offset = timestamp.utcoffset()
            if timestamp.tzinfo is None or offset is None or offset.total_seconds() != 0:
                raise ValueError("acquisition timestamps must be timezone-aware UTC")
        if self.acquisition_finished_at < self.acquisition_started_at:
            raise ValueError("finish precedes start")
        for duration_name, duration_value in (
            ("acquisition_duration", self.acquisition_duration),
            ("estimated_acquisition_duration", self.estimated_acquisition_duration),
        ):
            if not isfinite(duration_value) or duration_value < 0:
                raise ValueError(f"{duration_name} must be finite and non-negative")
        if not isfinite(self.acquisition_timeout_used) or self.acquisition_timeout_used <= 0:
            raise ValueError("acquisition_timeout_used must be finite and > 0")


GrabbedResponse: TypeAlias = tuple[int, DataDirection, Mapping[str, Any]]


def normalize_scan_images(
    responses: Iterable[GrabbedResponse],
) -> tuple[ScanChannelImage, ...]:
    """Validate FrameDataGrab responses without guessing row orientation."""
    images = []
    for channel_index, direction, response in responses:
        try:
            name = str(response["channel_name"])
            rows = int(response["scan_data_rows"])
            columns = int(response["scan_data_columns"])
            data = response["scan_data"]
            raw_scan_direction = int(response["scan_direction"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ScanResponseError(f"invalid Scan.FrameDataGrab response: {exc}") from exc
        if np.shape(data) != (rows, columns):
            raise ScanResponseError(
                f"FrameDataGrab shape {np.shape(data)} != declared ({rows}, {columns})"
            )
        if raw_scan_direction not in (0, 1):
            raise ScanResponseError(
                f"invalid FrameDataGrab scan direction {raw_scan_direction}"
            )
        images.append(
            ScanChannelImage(
                name=name,
                channel_index=channel_index,
                direction=direction,
                data=data,
                scan_direction="up" if raw_scan_direction == 1 else "down",
            )
        )
    return tuple(images)


def normalize_scan(
    images: Iterable[ScanChannelImage],
    *,
    saved_path: str,
    config: ScanConfig,
    effective: ScanSettings,
    acquisition_started_at: datetime,
    acquisition_finished_at: datetime,
    acquisition_duration: float,
    estimated_acquisition_duration: float,
    acquisition_timeout_used: float,
    nan_policy: NaNPolicy = NaNPolicy.WARN,
) -> ScanResult:
    result = ScanResult(
        images=tuple(images),
        frame=effective.frame,
        requested_config=config,
        effective_settings=effective,
        saved_path=saved_path,
        acquisition_started_at=acquisition_started_at,
        acquisition_finished_at=acquisition_finished_at,
        acquisition_duration=acquisition_duration,
        estimated_acquisition_duration=estimated_acquisition_duration,
        acquisition_timeout_used=acquisition_timeout_used,
    )
    return apply_scan_nan_policy(result, nan_policy)


def inspect_non_finite_scan_data(result: ScanResult) -> NonFiniteDiagnostics:
    nan_count = inf_count = 0
    fully_nan: list[str] = []
    affected: list[str] = []
    for image in result.images:
        nan_mask = np.isnan(image.data)
        inf_mask = np.isinf(image.data)
        label = f"{image.name} [{image.direction}]"
        nan_count += int(nan_mask.sum())
        inf_count += int(inf_mask.sum())
        if bool(np.all(nan_mask)):
            fully_nan.append(label)
        if bool(np.any(nan_mask | inf_mask)):
            affected.append(label)
    return NonFiniteDiagnostics(
        nan_count=nan_count,
        inf_count=inf_count,
        fully_nan_channels=tuple(fully_nan),
        affected_channels=tuple(affected),
    )


def apply_scan_nan_policy(result: ScanResult, policy: NaNPolicy) -> ScanResult:
    diagnostics = inspect_non_finite_scan_data(result)
    if not diagnostics.has_non_finite or policy is NaNPolicy.ALLOW:
        return result
    if policy is NaNPolicy.RAISE:
        raise NonFiniteScanDataError(result, diagnostics)
    logger.warning(
        "Scan data contains %d NaN and %d infinite values; affected images: %s",
        diagnostics.nan_count,
        diagnostics.inf_count,
        ", ".join(diagnostics.affected_channels),
    )
    return result
