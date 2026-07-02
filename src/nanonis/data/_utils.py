"""Internal immutable-array, metadata, and unit helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, cast

import numpy as np

from ..provenance import software_provenance as _software_provenance


def immutable_array(value: Any, *, ndim: int | None = None) -> np.ndarray:
    array = np.array(value, dtype=np.float64, copy=True)
    if ndim is not None and array.ndim != ndim:
        raise ValueError(f"expected a {ndim}-D array, got shape {array.shape}")
    array.setflags(write=False)
    return cast(np.ndarray, array)


def frozen_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return frozen_mapping(value)
    if isinstance(value, np.ndarray):
        array = np.array(value, copy=True)
        array.setflags(write=False)
        return array
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def metadata_value(value: Any) -> Any:
    """Convert frozen/Numpy values to JSON-compatible metadata values."""
    if isinstance(value, Mapping):
        return {str(key): metadata_value(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (tuple, list)):
        return [metadata_value(item) for item in value]
    return value


def software_provenance() -> dict[str, str]:
    """Backward-compatible delegate to the vertical-neutral helper."""
    return _software_provenance()


def controller_provenance(header: Mapping[str, Any]) -> dict[str, Any]:
    """Extract controller/file-format versions from heterogeneous headers."""
    normalized = {str(key).strip().lower(): value for key, value in header.items()}
    return {
        "nanonis_version": metadata_value(normalized.get("nanonis_version")),
        "software_version": metadata_value(
            normalized.get("nanonismain>sw version")
            or normalized.get("nanonis main>sw version")
            or normalized.get("sw version")
        ),
    }


def compact_header(header: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Select small acquisition facts without serializing the full raw header."""
    by_lower = {
        str(key).strip().lower(): (str(key), value) for key, value in header.items()
    }
    return {
        original: metadata_value(value)
        for key in keys
        if (item := by_lower.get(key.lower())) is not None
        for original, value in (item,)
    }


_LABEL_UNIT = re.compile(r"^(.*?)\s*[\[(]([^\])]+)[\])]\s*(.*)$")
_UNIT_SCALE: dict[str, tuple[str, float]] = {
    "": ("", 1.0),
    "1": ("", 1.0),
    "A": ("A", 1.0),
    "V": ("V", 1.0),
    "m": ("m", 1.0),
    "s": ("s", 1.0),
    "Hz": ("Hz", 1.0),
    "T": ("T", 1.0),
    "deg": ("deg", 1.0),
    "pA": ("A", 1e-12),
    "nA": ("A", 1e-9),
    "uA": ("A", 1e-6),
    "µA": ("A", 1e-6),
    "mA": ("A", 1e-3),
    "uV": ("V", 1e-6),
    "µV": ("V", 1e-6),
    "mV": ("V", 1e-3),
    "nm": ("m", 1e-9),
    "um": ("m", 1e-6),
    "µm": ("m", 1e-6),
    "mm": ("m", 1e-3),
    "us": ("s", 1e-6),
    "µs": ("s", 1e-6),
    "ms": ("s", 1e-3),
    "kHz": ("Hz", 1e3),
    "mT": ("T", 1e-3),
}


def split_label_unit(label: str) -> tuple[str, str]:
    match = _LABEL_UNIT.match(label.strip())
    if match is None:
        return label.strip(), ""
    name, unit, suffix = match.groups()
    suffix = suffix.strip()
    return f"{name.strip()} {suffix}".strip(), unit.strip()


def convert_to_si(values: Any, unit: str) -> tuple[np.ndarray, str]:
    normalized, scale = _UNIT_SCALE.get(unit.strip(), (unit.strip(), 1.0))
    array = np.asarray(values, dtype=np.float64)
    return array * scale, normalized


def unit_to_si(unit: str) -> tuple[str, float]:
    return _UNIT_SCALE.get(unit.strip(), (unit.strip(), 1.0))
