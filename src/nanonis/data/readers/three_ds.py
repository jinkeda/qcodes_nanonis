"""Reader for Nanonis 3DS grid-spectroscopy files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, cast

from ...geometry import FrameGeometry
from ...types import NaNPolicy
from .._utils import convert_to_si, split_label_unit
from ..models import Grid3DChannel, Grid3DData, SweepAxis
from ..validation import apply_nan_policy
from ._parser import parse_file


def read_3ds(
    path: str | Path, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> Grid3DData:
    """Read a grid-spectroscopy file into immutable SI-domain data."""
    source = Path(path)
    parsed, provenance = parse_file("3ds", source)
    header = cast(Mapping[str, Any], parsed.header)
    pixels, lines = (int(value) for value in header["dim_px"])
    center_x, center_y = (float(value) for value in header["pos_xy"])
    width, height = (float(value) for value in header["size_xy"])

    sweep_name, sweep_unit_raw = split_label_unit(str(header["sweep_signal"]))
    sweep_values, sweep_unit = convert_to_si(
        parsed.signals["sweep_signal"], sweep_unit_raw
    )
    channels = []
    for label in header["channels"]:
        name, raw_unit = split_label_unit(str(label))
        values, unit = convert_to_si(parsed.signals[str(label)], raw_unit)
        channels.append(Grid3DChannel(name, unit, values))

    labels = tuple(header.get("fixed_parameters", ())) + tuple(
        header.get("experimental_parameters", ())
    )
    params = parsed.signals["params"]
    parameters = {}
    for index, label in enumerate(labels):
        name, raw_unit = split_label_unit(str(label))
        values, _ = convert_to_si(params[:, :, index], raw_unit)
        parameters[name] = values

    result = Grid3DData(
        sweep_signal=SweepAxis(sweep_name, sweep_unit, sweep_values),
        channels=tuple(channels),
        fixed_parameters=parameters,
        region=FrameGeometry(
            center_x, center_y, width, height, float(header["angle"])
        ),
        pixels=pixels,
        lines=lines,
        header=header,
        source=str(source.resolve()),
        parser=provenance,
    )
    return cast(Grid3DData, apply_nan_policy(result, nan_policy))


__all__ = ["read_3ds"]
