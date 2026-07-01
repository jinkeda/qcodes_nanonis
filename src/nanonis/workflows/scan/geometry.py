"""Physical coordinate grids for scan images.

The frame geometry -- centre, width, height, and clockwise rotation -- is fully
known, so controller-coordinate X/Y grids for each pixel are well defined *except*
for one bit: whether image row 0 is the physical top or bottom edge (and, less
commonly, whether the fast axis runs left-to-right). That bit is a live-hardware
characterization result, so this module does not guess it -- ``row_order`` is a
required argument. Pass the value you have confirmed on the controller GUI / a
known surface feature; until then, treat the grids as provisional.

The rotation matches ``ScanFrame.corners()`` exactly (Nanonis positive angle is
clockwise)::

    x = center_x + local_x * cos(theta) + local_y * sin(theta)
    y = center_y - local_x * sin(theta) + local_y * cos(theta)
"""

from __future__ import annotations

from math import cos, radians, sin
from typing import Literal

import numpy as np

from .models import ScanRegion

RowOrder = Literal["top_to_bottom", "bottom_to_top"]
ColumnOrder = Literal["left_to_right", "right_to_left"]


def scan_coordinate_grids(
    frame: ScanRegion,
    pixels: int,
    lines: int,
    *,
    row_order: RowOrder,
    column_order: ColumnOrder = "left_to_right",
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(X, Y)`` pixel-centre controller coordinates, shape ``(lines, pixels)``.

    ``row_order`` is required and has no default: it encodes the unverified
    row-orientation bit, so the caller must state it explicitly. ``column_order``
    defaults to the forward/trace assumption (fast axis left to right).

    Coordinates are pixel centres (the ``(j + 0.5)`` convention), in metres, in the
    controller frame, with the frame's clockwise rotation applied.
    """
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
    frac = rows * (frame.height / lines)
    if row_order == "bottom_to_top":
        local_y = -frame.height / 2 + frac  # row 0 at the bottom edge
    else:
        local_y = frame.height / 2 - frac   # row 0 at the top edge

    local_xx, local_yy = np.meshgrid(local_x, local_y)  # (lines, pixels)
    theta = radians(frame.angle)
    cosine, sine = cos(theta), sin(theta)
    x = frame.center_x + local_xx * cosine + local_yy * sine
    y = frame.center_y - local_xx * sine + local_yy * cosine
    return x, y
