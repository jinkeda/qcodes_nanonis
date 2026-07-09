"""Acquire-first QCoDeS persistence for file-backed domain data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from qcodes.dataset.measurements import Measurement

from ..data.adapters.xarray import orient_sxm_array
from ..data.models import DataDirection, DatData, Grid3DData, SxmData
from ..geometry import scan_coordinate_grids


@dataclass(frozen=True)
class RegisteredSxm:
    row: str
    column: str
    x: str
    y: str
    channels: tuple[tuple[str, int, DataDirection], ...]


@dataclass(frozen=True)
class RegisteredGrid3D:
    row: str
    column: str
    sweep: str
    channels: tuple[tuple[str, int], ...]
    parameters: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RegisteredDat:
    sample: str
    columns: tuple[tuple[str, int], ...]


def create_sxm_measurement(
    experiment: Any, data: SxmData, *, station: Any = None, name: str = "SXM file"
) -> tuple[Measurement, RegisteredSxm]:
    measurement = Measurement(exp=experiment, station=station, name=name)
    return measurement, register_sxm_data(measurement, data)


def register_sxm_data(measurement: Any, data: SxmData) -> RegisteredSxm:
    row, column, x_name, y_name = "row_index", "column_index", "x_m", "y_m"
    _register(measurement, row, "Row index", "")
    _register(measurement, column, "Column index", "")
    setpoints = (row, column)
    _register(measurement, x_name, "Scan X", "m", setpoints)
    _register(measurement, y_name, "Scan Y", "m", setpoints)
    used = {row, column, x_name, y_name}
    registered = []
    for index, channel in enumerate(data.channels):
        for direction in channel.directions:
            parameter = _unique(_identifier(f"{channel.name}_{direction}"), used)
            used.add(parameter)
            _register(
                measurement,
                parameter,
                f"{channel.name} [{direction}]",
                channel.unit,
                setpoints,
            )
            registered.append((parameter, index, direction))
    return RegisteredSxm(row, column, x_name, y_name, tuple(registered))


def add_sxm_data(datasaver: Any, registered: RegisteredSxm, data: SxmData) -> None:
    column_index: np.ndarray
    row_index: np.ndarray
    column_index, row_index = np.meshgrid(
        np.arange(data.pixels), np.arange(data.lines)
    )
    x_grid, y_grid = scan_coordinate_grids(
        data.region,
        data.pixels,
        data.lines,
        row_order="top_to_bottom",
        column_order="left_to_right",
    )
    pairs: list[tuple[str, Any]] = [
        (registered.row, row_index),
        (registered.column, column_index),
        (registered.x, x_grid),
        (registered.y, y_grid),
    ]
    for parameter, channel_index, direction in registered.channels:
        channel = data.channels[channel_index]
        pairs.append(
            (
                parameter,
                orient_sxm_array(
                    channel.data(direction),
                    scan_direction=data.scan_direction,
                    data_direction=direction,
                ),
            )
        )
    datasaver.add_result(*pairs)
    _add_metadata(datasaver, data.to_metadata())


def create_grid_3ds_measurement(
    experiment: Any,
    data: Grid3DData,
    *,
    station: Any = None,
    name: str = "3DS file",
) -> tuple[Measurement, RegisteredGrid3D]:
    measurement = Measurement(exp=experiment, station=station, name=name)
    return measurement, register_grid_3ds_data(measurement, data)


def register_grid_3ds_data(
    measurement: Any, data: Grid3DData
) -> RegisteredGrid3D:
    row, column, sweep = "row_index", "column_index", "sweep"
    _register(measurement, row, "Row index", "")
    _register(measurement, column, "Column index", "")
    _register(
        measurement,
        sweep,
        data.sweep_signal.name,
        data.sweep_signal.unit,
    )
    setpoints = (row, column, sweep)
    used = {row, column, sweep}
    channels = []
    for index, channel in enumerate(data.channels):
        parameter = _unique(_identifier(channel.name), used)
        used.add(parameter)
        _register(measurement, parameter, channel.name, channel.unit, setpoints)
        channels.append((parameter, index))
    parameters = []
    for name in data.fixed_parameters:
        parameter = _unique(f"parameter_{_identifier(name)}", used)
        used.add(parameter)
        _register(measurement, parameter, name, "", (row, column))
        parameters.append((parameter, name))
    return RegisteredGrid3D(row, column, sweep, tuple(channels), tuple(parameters))


def add_grid_3ds_data(
    datasaver: Any, registered: RegisteredGrid3D, data: Grid3DData
) -> None:
    sweep_points = data.sweep_signal.values.size
    column_2d: np.ndarray
    row_2d: np.ndarray
    column_2d, row_2d = np.meshgrid(
        np.arange(data.pixels), np.arange(data.lines)
    )
    row_3d = np.broadcast_to(row_2d[:, :, None], (*row_2d.shape, sweep_points))
    column_3d = np.broadcast_to(
        column_2d[:, :, None], (*column_2d.shape, sweep_points)
    )
    sweep_3d = np.broadcast_to(
        data.sweep_signal.values, (data.lines, data.pixels, sweep_points)
    )
    pairs: list[tuple[str, Any]] = [
        (registered.row, row_3d),
        (registered.column, column_3d),
        (registered.sweep, sweep_3d),
    ]
    pairs.extend(
        (parameter, data.channels[index].values)
        for parameter, index in registered.channels
    )
    # QCoDeS requires setpoint shapes to match each dependent, so fixed maps are
    # emitted in a separate result with 2-D index grids.
    datasaver.add_result(*pairs)
    if registered.parameters:
        datasaver.add_result(
            (registered.row, row_2d),
            (registered.column, column_2d),
            *((parameter, data.fixed_parameters[name])
              for parameter, name in registered.parameters),
        )
    _add_metadata(datasaver, data.to_metadata())


def create_dat_measurement(
    experiment: Any, data: DatData, *, station: Any = None, name: str = "DAT file"
) -> tuple[Measurement, RegisteredDat]:
    measurement = Measurement(exp=experiment, station=station, name=name)
    return measurement, register_dat_data(measurement, data)


def register_dat_data(measurement: Any, data: DatData) -> RegisteredDat:
    sample = "sample_index"
    _register(measurement, sample, "Sample index", "")
    used = {sample}
    columns = []
    for index, column in enumerate(data.columns):
        parameter = _unique(_identifier(column.name), used)
        used.add(parameter)
        _register(measurement, parameter, column.name, column.unit, (sample,))
        columns.append((parameter, index))
    return RegisteredDat(sample, tuple(columns))


def add_dat_data(datasaver: Any, registered: RegisteredDat, data: DatData) -> None:
    pairs: list[tuple[str, Any]] = [
        (registered.sample, np.arange(data.points, dtype=int))
    ]
    pairs.extend(
        (parameter, data.columns[index].values)
        for parameter, index in registered.columns
    )
    datasaver.add_result(*pairs)
    _add_metadata(datasaver, data.to_metadata())


def _register(
    measurement: Any,
    name: str,
    label: str,
    unit: str,
    setpoints: tuple[str, ...] = (),
) -> None:
    kwargs: dict[str, Any] = {
        "label": label,
        "unit": unit,
        "paramtype": "array",
    }
    if setpoints:
        kwargs["setpoints"] = setpoints
    measurement.register_custom_parameter(name, **kwargs)


def _add_metadata(datasaver: Any, metadata: dict[str, Any]) -> None:
    dataset = getattr(datasaver, "dataset", None)
    if dataset is None or not hasattr(dataset, "add_metadata"):
        raise TypeError("datasaver must expose dataset.add_metadata")
    for key, value in metadata.items():
        dataset.add_metadata(key, json.dumps(value, default=str))


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    if not identifier:
        identifier = "value"
    return f"value_{identifier}" if identifier[0].isdigit() else identifier


def _unique(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    index = 2
    while f"{base}_{index}" in used:
        index += 1
    return f"{base}_{index}"


__all__ = [
    "RegisteredDat",
    "RegisteredGrid3D",
    "RegisteredSxm",
    "add_dat_data",
    "add_grid_3ds_data",
    "add_sxm_data",
    "create_dat_measurement",
    "create_grid_3ds_measurement",
    "create_sxm_measurement",
    "register_dat_data",
    "register_grid_3ds_data",
    "register_sxm_data",
]
