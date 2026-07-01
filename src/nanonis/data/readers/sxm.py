"""Reader for Nanonis SXM scan-image files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, cast

import numpy as np

from ...geometry import FrameGeometry
from ...types import NaNPolicy
from .._utils import convert_to_si
from ..models import DataDirection, SxmChannel, SxmData
from ..validation import apply_nan_policy
from ._parser import parse_file, parse_sxm_header_only


def read_sxm(
    path: str | Path, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> SxmData:
    """Read an SXM file without changing its stored row/column order."""
    source = Path(path)
    try:
        parsed, provenance = parse_file("sxm", source)
    except Exception:
        # Both released nanonispy and the pinned fork assume one global direction
        # count. Retain their header/offset layer and decode heterogeneous strides.
        parsed, provenance = parse_sxm_header_only(source)
        parsed.signals = _read_directional_payload(parsed)

    header = cast(Mapping[str, Any], parsed.header)
    data_info = cast(Mapping[str, Any], header["data_info"])
    names = tuple(str(value).strip() for value in data_info["Name"])
    units = tuple(str(value).strip() for value in data_info["Unit"])
    declared = tuple(str(value).strip().lower() for value in data_info["Direction"])
    if not (len(names) == len(units) == len(declared)):
        raise ValueError("SXM DATA_INFO columns have inconsistent lengths")

    channels = []
    for name, raw_unit, declaration in zip(names, units, declared):
        directions = _directions(declaration)
        signal = parsed.signals[name]
        converted: dict[DataDirection, np.ndarray | None] = {
            "forward": None,
            "backward": None,
        }
        unit = raw_unit
        for direction in directions:
            values, unit = convert_to_si(signal[direction], raw_unit)
            converted[direction] = values
        channels.append(
            SxmChannel(
                name=name,
                unit=unit,
                directions=directions,
                forward=converted["forward"],
                backward=converted["backward"],
            )
        )

    pixels, lines = (int(value) for value in header["scan_pixels"])
    width, height = (float(value) for value in header["scan_range"])
    center_x, center_y = (float(value) for value in header["scan_offset"])
    result = SxmData(
        channels=tuple(channels),
        region=FrameGeometry(
            center_x, center_y, width, height, float(header["scan_angle"])
        ),
        pixels=pixels,
        lines=lines,
        scan_direction=str(header["scan_dir"]).strip().lower(),  # type: ignore[arg-type]
        header=header,
        source=str(source.resolve()),
        parser=provenance,
    )
    return cast(SxmData, apply_nan_policy(result, nan_policy))


def _directions(value: str) -> tuple[DataDirection, ...]:
    normalized = value.lower()
    if normalized == "both":
        return ("forward", "backward")
    if normalized in ("fwd", "forward"):
        return ("forward",)
    if normalized in ("bwd", "backward"):
        return ("backward",)
    raise ValueError(f"unsupported SXM DATA_INFO direction {value!r}")


def _read_directional_payload(parsed: Any) -> dict[str, dict[str, np.ndarray]]:
    info = parsed.header["data_info"]
    names = tuple(str(value).strip() for value in info["Name"])
    directions = tuple(_directions(str(value)) for value in info["Direction"])
    pixels, lines = (int(value) for value in parsed.header["scan_pixels"])
    frame_size = pixels * lines
    with open(parsed.fname, "rb") as handle:
        handle.seek(parsed.byte_offset)
        payload = np.fromfile(handle, dtype=parsed.data_format)
    expected = sum(len(value) for value in directions) * frame_size
    if payload.size != expected:
        raise ValueError(
            f"SXM payload has {payload.size} values; expected {expected} "
            "from DATA_INFO"
        )
    output: dict[str, dict[str, np.ndarray]] = {}
    offset = 0
    for name, available in zip(names, directions):
        output[name] = {}
        for direction in available:
            stop = offset + frame_size
            output[name][direction] = payload[offset:stop].reshape(lines, pixels)
            offset = stop
    return output


__all__ = ["read_sxm"]
