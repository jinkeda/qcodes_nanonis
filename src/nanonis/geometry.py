"""Hardware-free scan-frame geometry and physical coordinate grids."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, radians, sin
from typing import Literal, Protocol

import numpy as np

RowOrder = Literal["top_to_bottom", "bottom_to_top"]
ColumnOrder = Literal["left_to_right", "right_to_left"]


class GeometryLike(Protocol):
    @property
    def center_x(self) -> float: ...

    @property
    def center_y(self) -> float: ...

    @property
    def width(self) -> float: ...

    @property
    def height(self) -> float: ...

    @property
    def angle(self) -> float: ...


@dataclass(frozen=True)
class FrameGeometry:
    """A rotated rectangular frame in controller coordinates (SI units)."""

    center_x: float
    center_y: float
    width: float
    height: float
    angle: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("center_x", self.center_x),
            ("center_y", self.center_y),
            ("angle", self.angle),
        ):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        for name, value in (("width", self.width), ("height", self.height)):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")

    def corners(self) -> tuple[tuple[float, float], ...]:
        """Return frame corners using Nanonis' clockwise-positive angle."""
        theta = radians(self.angle)
        cosine, sine = cos(theta), sin(theta)
        return tuple(
            (
                self.center_x + local_x * cosine + local_y * sine,
                self.center_y - local_x * sine + local_y * cosine,
            )
            for local_x, local_y in (
                (-self.width / 2, -self.height / 2),
                (-self.width / 2, self.height / 2),
                (self.width / 2, -self.height / 2),
                (self.width / 2, self.height / 2),
            )
        )


def scan_coordinate_grids(
    frame: GeometryLike,
    pixels: int,
    lines: int,
    *,
    row_order: RowOrder,
    column_order: ColumnOrder = "left_to_right",
) -> tuple[np.ndarray, np.ndarray]:
    """Return pixel-centre X/Y grids in controller coordinates."""
    if pixels < 1 or lines < 1:
        raise ValueError("pixels and lines must be >= 1")
    if row_order not in ("top_to_bottom", "bottom_to_top"):
        raise ValueError("row_order must be 'top_to_bottom' or 'bottom_to_top'")
    if column_order not in ("left_to_right", "right_to_left"):
        raise ValueError("column_order must be 'left_to_right' or 'right_to_left'")

    cols = np.arange(pixels, dtype=float) + 0.5
    if column_order == "right_to_left":
        cols = pixels - cols
    local_x = -frame.width / 2 + cols * (frame.width / pixels)

    rows = np.arange(lines, dtype=float) + 0.5
    fraction = rows * (frame.height / lines)
    local_y = (
        -frame.height / 2 + fraction
        if row_order == "bottom_to_top"
        else frame.height / 2 - fraction
    )
    local_xx: np.ndarray
    local_yy: np.ndarray
    local_xx, local_yy = np.meshgrid(local_x, local_y)
    theta = radians(frame.angle)
    cosine, sine = cos(theta), sin(theta)
    return (
        frame.center_x + local_xx * cosine + local_yy * sine,
        frame.center_y - local_xx * sine + local_yy * cosine,
    )


__all__ = [
    "ColumnOrder",
    "FrameGeometry",
    "GeometryLike",
    "RowOrder",
    "scan_coordinate_grids",
]
