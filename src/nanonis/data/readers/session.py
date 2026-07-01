"""Explicit reader for Nanonis session configuration snapshots."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, TypeAlias

SessionValue: TypeAlias = str | int | float | bool


@dataclass(frozen=True)
class SessionModule:
    name: str
    values: Mapping[str, SessionValue]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True)
class SessionConfig:
    modules: Mapping[str, SessionModule]
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "modules", MappingProxyType(dict(self.modules)))

    def module(self, name: str) -> SessionModule | None:
        return self.modules.get(name)

    @property
    def lock_in(self) -> SessionModule | None:
        return self.module("LockInADV") or self.module("LockInFPGA")

    @property
    def atom_tracking(self) -> SessionModule | None:
        return self.module("Atom Tracking")

    @property
    def bias_spectroscopy(self) -> SessionModule | None:
        return self.module("Bias Spectroscopy")

    def to_metadata(self) -> dict[str, object]:
        return {
            "format": "nanonis-session",
            "source": self.source,
            "sections": list(self.modules),
        }


def read_session(path: str | Path) -> SessionConfig:
    """Read a session INI independently of measurement-file readers."""
    source = Path(path)
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str  # type: ignore[method-assign,assignment]
    with source.open("r", encoding="utf-8", errors="replace") as handle:
        parser.read_file(handle)
    modules = {
        section: SessionModule(
            section,
            {name: _typed_value(value) for name, value in parser.items(section)},
        )
        for section in parser.sections()
    }
    return SessionConfig(modules, str(source.resolve()))


def _typed_value(value: str) -> SessionValue:
    stripped = value.strip().strip('"')
    if stripped.upper() in ("TRUE", "FALSE"):
        return stripped.upper() == "TRUE"
    try:
        return int(stripped)
    except ValueError:
        try:
            return float(stripped)
        except ValueError:
            return stripped


__all__ = ["SessionConfig", "SessionModule", "SessionValue", "read_session"]
