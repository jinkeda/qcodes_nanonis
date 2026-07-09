"""Optional xarray adapters for immutable Nanonis domain data."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from ...geometry import ColumnOrder, RowOrder, scan_coordinate_grids
from ..models import DatData, DataDirection, Grid3DData, SxmData

if TYPE_CHECKING:
    import xarray as xr

logger = logging.getLogger(__name__)


def sxm_raw_orders(
    scan_direction: str, data_direction: DataDirection
) -> tuple[RowOrder, ColumnOrder]:
    """Return physical orders of the untouched SXM payload."""
    if scan_direction not in ("up", "down"):
        raise ValueError("scan_direction must be 'up' or 'down'")
    row: RowOrder = "bottom_to_top" if scan_direction == "up" else "top_to_bottom"
    column: ColumnOrder = (
        "right_to_left" if data_direction == "backward" else "left_to_right"
    )
    return row, column


def orient_sxm_array(
    values: np.ndarray,
    *,
    scan_direction: str,
    data_direction: DataDirection,
) -> np.ndarray:
    """Apply the confirmed SXM file convention to physical top/left order."""
    output = np.asarray(values)
    if scan_direction == "up":
        output = np.flip(output, axis=0)
    elif scan_direction != "down":
        raise ValueError("scan_direction must be 'up' or 'down'")
    if data_direction == "backward":
        output = np.flip(output, axis=1)
    return cast(np.ndarray, output)


def sxm_to_xarray(data: SxmData) -> "xr.Dataset":
    """Build an oriented Dataset with 2-D physical controller coordinates."""
    xr = _xarray()
    x_grid, y_grid = scan_coordinate_grids(
        data.region,
        data.pixels,
        data.lines,
        row_order="top_to_bottom",
        column_order="left_to_right",
    )
    variables: dict[str, Any] = {}
    used: set[str] = set()
    for channel in data.channels:
        for direction in channel.directions:
            name = _unique(f"{_identifier(channel.name)}_{direction}", used)
            used.add(name)
            variables[name] = xr.DataArray(
                orient_sxm_array(
                    channel.data(direction),
                    scan_direction=data.scan_direction,
                    data_direction=direction,
                ),
                dims=("row", "column"),
                attrs={
                    "long_name": channel.name,
                    "units": channel.unit,
                    "data_direction": direction,
                    "raw_scan_direction": data.scan_direction,
                },
            )
    metadata = data.to_metadata()
    metadata.pop("header", None)
    return xr.Dataset(
        variables,
        coords={
            "row": np.arange(data.lines),
            "column": np.arange(data.pixels),
            "x_m": (("row", "column"), x_grid),
            "y_m": (("row", "column"), y_grid),
        },
        attrs=metadata,
    )


def grid_3ds_to_xarray(
    data: Grid3DData,
    *,
    row_order: RowOrder,
    column_order: ColumnOrder = "left_to_right",
) -> "xr.Dataset":
    """Build a Dataset using caller-declared, unverified raw grid orientation.

    Unlike SXM, this rig's 3DS file orientation has no paired acquisition oracle.
    The cube is therefore never flipped here: the required ``row_order`` and
    optional ``column_order`` describe how its existing matrix indexes map to the
    physical frame.
    """
    xr = _xarray()
    logger.warning(
        "3DS raw orientation is not ground-truth validated; using "
        "row_order=%r and column_order=%r without flipping the cube",
        row_order,
        column_order,
    )
    x_grid, y_grid = scan_coordinate_grids(
        data.region,
        data.pixels,
        data.lines,
        row_order=row_order,
        column_order=column_order,
    )
    variables: dict[str, Any] = {}
    used: set[str] = set()
    for channel in data.channels:
        name = _unique(_identifier(channel.name), used)
        used.add(name)
        variables[name] = xr.DataArray(
            channel.values,
            dims=("row", "column", "sweep"),
            attrs={"long_name": channel.name, "units": channel.unit},
        )
    for parameter, values in data.fixed_parameters.items():
        name = _unique(f"parameter_{_identifier(parameter)}", used)
        used.add(name)
        variables[name] = xr.DataArray(
            values,
            dims=("row", "column"),
            attrs={"long_name": parameter},
        )
    metadata = data.to_metadata()
    metadata["raw_row_order"] = row_order
    metadata["raw_column_order"] = column_order
    metadata["orientation_ground_truth_validated"] = False
    return xr.Dataset(
        variables,
        coords={
            "row": np.arange(data.lines),
            "column": np.arange(data.pixels),
            "sweep": data.sweep_signal.values,
            "x_m": (("row", "column"), x_grid),
            "y_m": (("row", "column"), y_grid),
        },
        attrs=metadata,
    )


def dat_to_xarray(data: DatData) -> "xr.Dataset":
    xr = _xarray()
    variables: dict[str, Any] = {}
    used: set[str] = set()
    for column in data.columns:
        name = _unique(_identifier(column.name), used)
        used.add(name)
        variables[name] = xr.DataArray(
            column.values,
            dims=("sample",),
            attrs={"long_name": column.name, "units": column.unit},
        )
    metadata = data.to_metadata()
    metadata.pop("header", None)
    return xr.Dataset(
        variables,
        coords={"sample": np.arange(data.points)},
        attrs=metadata,
    )


def _xarray() -> Any:
    try:
        import xarray
    except ImportError as exc:
        raise ImportError(
            "xarray adapters require the optional 'xarray' dependency"
        ) from exc
    return xarray


def _identifier(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    if not value:
        value = "value"
    return f"value_{value}" if value[0].isdigit() else value


def _unique(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    index = 2
    while f"{base}_{index}" in used:
        index += 1
    return f"{base}_{index}"


__all__ = [
    "dat_to_xarray",
    "grid_3ds_to_xarray",
    "orient_sxm_array",
    "sxm_raw_orders",
    "sxm_to_xarray",
]
