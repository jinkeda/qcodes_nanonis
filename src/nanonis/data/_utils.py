"""Internal immutable-array, metadata, and unit helpers."""

from __future__ import annotations

import re
import os
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import numpy as np


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
    """Return package version and source commit when a checkout is available."""
    try:
        package_version = version("qcodes-nanonis")
    except PackageNotFoundError:
        package_version = "0.1.0"
    commit = os.environ.get("QCODES_NANONIS_GIT_COMMIT") or _source_git_commit()
    return {
        "name": "qcodes-nanonis",
        "version": package_version,
        "git_commit": commit or "unknown",
    }


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


def compact_header(
    header: Mapping[str, Any], keys: tuple[str, ...]
) -> dict[str, Any]:
    """Select small acquisition facts without serializing the full raw header."""
    by_lower = {str(key).strip().lower(): (str(key), value)
                for key, value in header.items()}
    return {
        original: metadata_value(value)
        for key in keys
        if (item := by_lower.get(key.lower())) is not None
        for original, value in (item,)
    }


def _source_git_commit() -> str | None:
    for parent in Path(__file__).resolve().parents:
        marker = parent / ".git"
        if marker.is_dir():
            return _read_git_dir(marker)
        if marker.is_file():
            line = marker.read_text(encoding="utf-8", errors="replace").strip()
            if line.startswith("gitdir:"):
                git_dir = (parent / line.split(":", 1)[1].strip()).resolve()
                return _read_git_dir(git_dir)
    return None


def _read_git_dir(git_dir: Path) -> str | None:
    head_path = git_dir / "HEAD"
    if not head_path.is_file():
        return None
    head = head_path.read_text(encoding="ascii", errors="replace").strip()
    if not head.startswith("ref:"):
        return head or None
    reference = head.split(":", 1)[1].strip()
    loose = git_dir / reference
    if loose.is_file():
        return loose.read_text(encoding="ascii", errors="replace").strip() or None
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii", errors="replace").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == reference:
                    return commit
    return None


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
