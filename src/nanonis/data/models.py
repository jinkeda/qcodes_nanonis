"""Immutable STM domain models returned by Nanonis file readers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

import numpy as np

from ..geometry import FrameGeometry
from ._utils import (
    compact_header,
    controller_provenance,
    frozen_mapping,
    immutable_array,
    metadata_value,
    software_provenance,
)

DataDirection = Literal["forward", "backward"]


@dataclass(frozen=True)
class ParserProvenance:
    name: str
    version: str


@dataclass(frozen=True)
class SxmChannel:
    name: str
    unit: str
    directions: tuple[DataDirection, ...]
    forward: np.ndarray | None = None
    backward: np.ndarray | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("SXM channel name must not be empty")
        if not self.unit.strip():
            raise ValueError(f"SXM channel {self.name!r} has no unit")
        directions = tuple(self.directions)
        if not directions or len(set(directions)) != len(directions):
            raise ValueError(f"invalid directions for SXM channel {self.name!r}")
        if any(value not in ("forward", "backward") for value in directions):
            raise ValueError(f"invalid direction for SXM channel {self.name!r}")
        object.__setattr__(self, "directions", directions)
        for direction in ("forward", "backward"):
            value = getattr(self, direction)
            if value is not None:
                object.__setattr__(self, direction, immutable_array(value, ndim=2))
            if (direction in directions) != (value is not None):
                raise ValueError(
                    f"SXM channel {self.name!r} direction availability is inconsistent"
                )

    def data(self, direction: DataDirection) -> np.ndarray:
        value = self.forward if direction == "forward" else self.backward
        if value is None:
            raise KeyError(f"{self.name!r} has no {direction} frame")
        return value


@dataclass(frozen=True)
class SxmData:
    channels: tuple[SxmChannel, ...]
    region: FrameGeometry
    pixels: int
    lines: int
    scan_direction: Literal["up", "down"]
    header: Mapping[str, Any]
    source: str
    parser: ParserProvenance

    def __post_init__(self) -> None:
        channels = tuple(self.channels)
        object.__setattr__(self, "channels", channels)
        object.__setattr__(self, "header", frozen_mapping(self.header))
        if self.pixels < 1 or self.lines < 1:
            raise ValueError("SXM dimensions must be positive")
        if self.scan_direction not in ("up", "down"):
            raise ValueError("SXM scan_direction must be 'up' or 'down'")
        _unique_names((channel.name for channel in channels), "SXM channel")
        expected = (self.lines, self.pixels)
        for channel in channels:
            for direction in channel.directions:
                if channel.data(direction).shape != expected:
                    raise ValueError(
                        f"{channel.name!r} {direction} shape "
                        f"{channel.data(direction).shape} != {expected}"
                    )

    def to_metadata(self, *, include_header: bool = False) -> dict[str, Any]:
        metadata = {
            "format": "sxm",
            "source": str(Path(self.source)),
            "parser": asdict(self.parser),
            "software": software_provenance(),
            "controller": controller_provenance(self.header),
            "pixels": self.pixels,
            "lines": self.lines,
            "scan_direction": self.scan_direction,
            "region": asdict(self.region),
            "channels": [
                {"name": channel.name, "unit": channel.unit,
                 "directions": list(channel.directions)}
                for channel in self.channels
            ],
            "header_summary": compact_header(
                self.header,
                ("rec_date", "rec_time", "scan_file", "comment"),
            ),
        }
        if include_header:
            metadata["header"] = metadata_value(self.header)
        return metadata


@dataclass(frozen=True)
class SweepAxis:
    name: str
    unit: str
    values: np.ndarray

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.unit.strip():
            raise ValueError("sweep name and unit are required")
        values = immutable_array(self.values, ndim=1)
        if not values.size:
            raise ValueError("sweep axis must not be empty")
        # Validate the finite subsequence so missing points remain governed by
        # NaNPolicy. Interspersed NaNs are retained, not treated as sweep turns.
        finite = values[np.isfinite(values)]
        differences = np.diff(finite)
        if np.any(differences > 0) and np.any(differences < 0):
            raise ValueError("sweep axis must be monotonic")
        object.__setattr__(self, "values", values)

    @property
    def direction(self) -> Literal["increasing", "decreasing", "constant"]:
        finite = self.values[np.isfinite(self.values)]
        differences = np.diff(finite)
        if np.any(differences > 0):
            return "increasing"
        if np.any(differences < 0):
            return "decreasing"
        return "constant"


@dataclass(frozen=True)
class Grid3DChannel:
    name: str
    unit: str
    values: np.ndarray

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.unit.strip():
            raise ValueError("grid channel name and unit are required")
        object.__setattr__(self, "values", immutable_array(self.values, ndim=3))


@dataclass(frozen=True)
class Grid3DData:
    sweep_signal: SweepAxis
    channels: tuple[Grid3DChannel, ...]
    fixed_parameters: Mapping[str, np.ndarray]
    region: FrameGeometry
    pixels: int
    lines: int
    header: Mapping[str, Any]
    source: str
    parser: ParserProvenance

    def __post_init__(self) -> None:
        channels = tuple(self.channels)
        object.__setattr__(self, "channels", channels)
        object.__setattr__(self, "header", frozen_mapping(self.header))
        parameters = {
            str(name): immutable_array(values, ndim=2)
            for name, values in self.fixed_parameters.items()
        }
        object.__setattr__(self, "fixed_parameters", frozen_mapping(parameters))
        _unique_names((channel.name for channel in channels), "grid channel")
        _unique_names(parameters, "grid parameter")
        expected_cube = (self.lines, self.pixels, self.sweep_signal.values.size)
        expected_map = (self.lines, self.pixels)
        for channel in channels:
            if channel.values.shape != expected_cube:
                raise ValueError(
                    f"grid channel {channel.name!r} shape {channel.values.shape} "
                    f"!= {expected_cube}"
                )
        for name, values in parameters.items():
            if values.shape != expected_map:
                raise ValueError(
                    f"grid parameter {name!r} shape {values.shape} != {expected_map}"
                )

    def to_metadata(self, *, include_header: bool = False) -> dict[str, Any]:
        metadata = {
            "format": "3ds",
            "source": str(Path(self.source)),
            "parser": asdict(self.parser),
            "software": software_provenance(),
            "controller": controller_provenance(self.header),
            "pixels": self.pixels,
            "lines": self.lines,
            "region": asdict(self.region),
            "sweep": {
                "name": self.sweep_signal.name,
                "unit": self.sweep_signal.unit,
                "points": int(self.sweep_signal.values.size),
            },
            "channels": [
                {"name": channel.name, "unit": channel.unit}
                for channel in self.channels
            ],
            "fixed_parameters": list(self.fixed_parameters),
            "header_summary": compact_header(
                self.header,
                ("experiment_name", "start_time", "end_time", "user", "comment"),
            ),
        }
        if include_header:
            metadata["header"] = metadata_value(self.header)
        return metadata


@dataclass(frozen=True)
class DatColumn:
    name: str
    unit: str
    values: np.ndarray

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("DAT column name must not be empty")
        object.__setattr__(self, "values", immutable_array(self.values, ndim=1))


@dataclass(frozen=True)
class DatData:
    columns: tuple[DatColumn, ...]
    header: Mapping[str, Any]
    source: str
    parser: ParserProvenance

    def __post_init__(self) -> None:
        columns = tuple(self.columns)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "header", frozen_mapping(self.header))
        _unique_names((column.name for column in columns), "DAT column")
        sizes = {column.values.size for column in columns}
        if len(sizes) > 1:
            raise ValueError("DAT columns have different lengths")

    @property
    def points(self) -> int:
        return int(self.columns[0].values.size) if self.columns else 0

    def to_metadata(self, *, include_header: bool = False) -> dict[str, Any]:
        metadata = {
            "format": "dat",
            "source": str(Path(self.source)),
            "parser": asdict(self.parser),
            "software": software_provenance(),
            "controller": controller_provenance(self.header),
            "points": self.points,
            "columns": [
                {"name": column.name, "unit": column.unit}
                for column in self.columns
            ],
            "header_summary": compact_header(
                self.header,
                ("Experiment", "Saved Date", "Start time", "User", "Date"),
            ),
        }
        if include_header:
            metadata["header"] = metadata_value(self.header)
        return metadata


def _unique_names(names: Any, label: str) -> None:
    values = tuple(names)
    if len(set(values)) != len(values):
        raise ValueError(f"{label} names must be unique")


__all__ = [
    "DatColumn",
    "DatData",
    "DataDirection",
    "Grid3DChannel",
    "Grid3DData",
    "ParserProvenance",
    "SxmChannel",
    "SxmData",
    "SweepAxis",
]
