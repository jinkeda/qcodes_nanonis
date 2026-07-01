"""Acquire-first QCoDeS persistence for scan results.

Formerly a deferred stub. The one thing that gated it -- ``FrameDataGrab`` row
orientation -- was characterized live on 2026-07-01 (see the scan walkthrough's
addendum): the buffer is *physically indexed* with ``row_order = "top_to_bottom"``
(matrix row 0 is the frame's top edge; *up*/*down* do not reverse it). That closes
the gate, so this adapter now persists a completed :class:`ScanResult`.

Model (per the plan's recorded QCoDeS-0.54 finding): each 2-D image's setpoints
must be **2-D meshgrids of the same ``(lines, pixels)`` shape** -- 1-D axes are
rejected. This adapter registers mandatory integer index meshgrids
(``row_index`` / ``col_index``) as the setpoints, then registers every channel
image -- and, optionally, physical ``x_m`` / ``y_m`` controller-coordinate grids --
as dependents sharing those setpoints. Physical grids use the confirmed
``row_order`` and the frame's rotation; the **fast-axis** ``column_order`` is not
yet characterized, so it is an explicit parameter (default ``"left_to_right"``)
and a warning is logged when physical coordinates are emitted.

Like the spectroscopy adapter, this consumes an already-acquired result; it never
controls hardware.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from qcodes.dataset.measurements import Measurement

from ..workflows.scan import ScanResult, scan_coordinate_grids
from ..workflows.scan.geometry import ColumnOrder, RowOrder
from ..workflows.scan.models import DataDirection

logger = logging.getLogger(__name__)

# Confirmed live (6501 rig); see scan_workflow_walkthrough.md 2026-07-01 addendum.
DEFAULT_ROW_ORDER: RowOrder = "top_to_bottom"
# Fast axis not yet characterized; the forward/trace assumption from geometry.py.
DEFAULT_COLUMN_ORDER: ColumnOrder = "left_to_right"


@dataclass(frozen=True)
class RegisteredScanChannel:
    parameter_name: str
    label: str
    channel_index: int
    direction: DataDirection


@dataclass(frozen=True)
class RegisteredScan:
    row_index_name: str
    col_index_name: str
    x_name: str | None
    y_name: str | None
    channels: tuple[RegisteredScanChannel, ...]
    shape: tuple[int, int]           # (lines, pixels)
    row_order: RowOrder
    column_order: ColumnOrder


def create_scan_measurement(
    experiment: Any,
    result: ScanResult,
    *,
    station: Any = None,
    name: str = "scan",
    row_order: RowOrder = DEFAULT_ROW_ORDER,
    column_order: ColumnOrder = DEFAULT_COLUMN_ORDER,
    physical_coordinates: bool = True,
) -> tuple[Measurement, RegisteredScan]:
    """Create and register a QCoDeS measurement from an acquired scan result."""
    measurement = Measurement(exp=experiment, station=station, name=name)
    registered = register_scan_result(
        measurement,
        result,
        row_order=row_order,
        column_order=column_order,
        physical_coordinates=physical_coordinates,
    )
    return measurement, registered


def register_scan_result(
    measurement: Any,
    result: ScanResult,
    *,
    row_order: RowOrder = DEFAULT_ROW_ORDER,
    column_order: ColumnOrder = DEFAULT_COLUMN_ORDER,
    physical_coordinates: bool = True,
) -> RegisteredScan:
    """Register index setpoints and image (and optional coordinate) parameters.

    Call before ``measurement.run``. Every image must share one ``(lines,
    pixels)`` shape; channel/direction pairs are unique by construction of
    :class:`ScanResult`, and are disambiguated into unique QCoDeS identifiers.
    """
    images = result.images
    if not images:
        raise ValueError("scan result has no images to persist")
    shape = (images[0].rows, images[0].columns)
    for image in images:
        if (image.rows, image.columns) != shape:
            raise ValueError(
                "all scan images must share one (lines, pixels) shape; "
                f"got {shape} and {(image.rows, image.columns)}"
            )

    row_index_name, col_index_name = "row_index", "col_index"
    measurement.register_custom_parameter(
        row_index_name, label="Row index", unit="", paramtype="array"
    )
    measurement.register_custom_parameter(
        col_index_name, label="Column index", unit="", paramtype="array"
    )
    setpoints = (row_index_name, col_index_name)
    used = {row_index_name, col_index_name}

    x_name: str | None = None
    y_name: str | None = None
    if physical_coordinates:
        x_name, y_name = "x_m", "y_m"
        used.update((x_name, y_name))
        measurement.register_custom_parameter(
            x_name, label="Scan X", unit="m", setpoints=setpoints, paramtype="array"
        )
        measurement.register_custom_parameter(
            y_name, label="Scan Y", unit="m", setpoints=setpoints, paramtype="array"
        )
        logger.warning(
            "Persisting physical x_m/y_m grids with row_order=%r (confirmed) and "
            "column_order=%r (fast axis NOT characterized): X may be mirrored until "
            "column_order is verified. Pass the confirmed column_order, or set "
            "physical_coordinates=False to store only the unambiguous index grids.",
            row_order,
            column_order,
        )

    channels: list[RegisteredScanChannel] = []
    for image in images:
        base = f"{_sanitize_identifier(image.name)}_{image.direction}"
        parameter_name = _unique_identifier(base, used)
        used.add(parameter_name)
        measurement.register_custom_parameter(
            parameter_name,
            label=f"{image.name} [{image.direction}]",
            unit=_unit_from_label(image.name),
            setpoints=setpoints,
            paramtype="array",
        )
        channels.append(
            RegisteredScanChannel(
                parameter_name, image.name, image.channel_index, image.direction
            )
        )

    return RegisteredScan(
        row_index_name=row_index_name,
        col_index_name=col_index_name,
        x_name=x_name,
        y_name=y_name,
        channels=tuple(channels),
        shape=shape,
        row_order=row_order,
        column_order=column_order,
    )


def add_scan_result(
    datasaver: Any, registered: RegisteredScan, result: ScanResult
) -> None:
    """Insert one complete scan result and its acquisition metadata."""
    images = {(img.channel_index, img.direction): img for img in result.images}
    if len(images) != len(registered.channels):
        raise ValueError("registered channel schema does not match result images")

    rows, cols = registered.shape
    col_idx, row_idx = np.meshgrid(np.arange(cols), np.arange(rows))  # each (rows, cols)
    pairs: list[tuple[str, Any]] = [
        (registered.row_index_name, row_idx),
        (registered.col_index_name, col_idx),
    ]
    if registered.x_name is not None and registered.y_name is not None:
        x_grid, y_grid = scan_coordinate_grids(
            result.frame,
            cols,
            rows,
            row_order=registered.row_order,
            column_order=registered.column_order,
        )
        pairs.append((registered.x_name, x_grid))
        pairs.append((registered.y_name, y_grid))

    for channel in registered.channels:
        image = images.get((channel.channel_index, channel.direction))
        if image is None:
            raise ValueError(
                f"result missing image for channel {channel.channel_index} "
                f"[{channel.direction}]"
            )
        data = np.asarray(image.data)
        if data.shape != registered.shape:
            raise ValueError(
                "image shape changed since registration: "
                f"{registered.shape} -> {data.shape}"
            )
        pairs.append((channel.parameter_name, data))
    datasaver.add_result(*pairs)

    metadata = {
        "acquisition_started_at": result.acquisition_started_at.isoformat(),
        "acquisition_finished_at": result.acquisition_finished_at.isoformat(),
        "acquisition_duration_s": result.acquisition_duration,
        "estimated_acquisition_duration_s": result.estimated_acquisition_duration,
        "acquisition_timeout_used_s": result.acquisition_timeout_used,
        "saved_path": result.saved_path,
        "row_order": registered.row_order,
        "column_order": registered.column_order,
        "frame": _json_safe(asdict(result.frame)),
        "requested_region": (
            _json_safe(asdict(result.requested_region))
            if result.requested_region is not None
            else None
        ),
        "requested_config": _json_safe(asdict(result.requested_config)),
        "effective_settings": _json_safe(asdict(result.effective_settings)),
        "images": json.dumps(
            [
                {
                    "channel_index": channel.channel_index,
                    "name": channel.label,
                    "direction": channel.direction,
                }
                for channel in registered.channels
            ]
        ),
    }
    dataset = getattr(datasaver, "dataset", None)
    if dataset is None or not hasattr(dataset, "add_metadata"):
        raise TypeError("datasaver must expose dataset.add_metadata")
    for key, value in metadata.items():
        dataset.add_metadata(key, value)


def _json_safe(obj: Any) -> str:
    """Serialize provenance without failing on non-JSON values (enums, tuples)."""
    return json.dumps(obj, default=str)


def _sanitize_identifier(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    identifier = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    if not identifier:
        identifier = "channel"
    if identifier[0].isdigit():
        identifier = f"channel_{identifier}"
    return identifier


def _unique_identifier(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    occurrence = 2
    while f"{base}_{occurrence}" in used:
        occurrence += 1
    return f"{base}_{occurrence}"


def _unit_from_label(label: str) -> str:
    match = re.search(r"\(([^()]*)\)\s*(?:\[[^]]+\])?$", label)
    return match.group(1) if match else ""


__all__ = [
    "RegisteredScan",
    "RegisteredScanChannel",
    "add_scan_result",
    "create_scan_measurement",
    "register_scan_result",
]
