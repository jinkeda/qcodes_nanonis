"""Reader for column-oriented Nanonis DAT files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, cast

from ...types import NaNPolicy
from .._utils import convert_to_si, split_label_unit
from ..models import DatColumn, DatData
from ..validation import apply_nan_policy
from ._parser import parse_file


def read_dat(
    path: str | Path, *, nan_policy: NaNPolicy = NaNPolicy.WARN
) -> DatData:
    """Read a column-oriented DAT file through the nanonispy parser.

    Regression coverage currently exists for the bias-spectroscopy fixture only.
    """
    source = Path(path)
    parsed, provenance = parse_file("dat", source)
    columns = []
    for label, raw_values in parsed.signals.items():
        name, raw_unit = split_label_unit(str(label))
        values, unit = convert_to_si(raw_values, raw_unit)
        columns.append(DatColumn(name, unit, values))
    result = DatData(
        columns=tuple(columns),
        header=cast(Mapping[str, Any], parsed.header),
        source=str(source.resolve()),
        parser=provenance,
    )
    return cast(DatData, apply_nan_policy(result, nan_policy))


__all__ = ["read_dat"]
