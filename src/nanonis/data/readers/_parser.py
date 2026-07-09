"""Compatibility boundary around supported nanonispy implementations."""

from __future__ import annotations

from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from ..models import ParserProvenance


def parse_file(kind: str, path: str | Path) -> tuple[Any, ParserProvenance]:
    parser_class, provenance, legacy = _parser_class(kind)
    with _legacy_numpy_aliases(legacy):
        return parser_class(str(path)), provenance


def parse_sxm_header_only(
    path: str | Path,
) -> tuple[Any, ParserProvenance]:
    """Use nanonispy's base/header parser without its uniform-direction reshape."""
    try:
        from nanonispy2.core.base import NanonisFile
        from nanonispy2.io.formats import get_dtype
        from nanonispy2.parsers.header import parse_scan_header

        base = object.__new__(NanonisFile)
        NanonisFile.__init__(base, str(path))
        base.data_format = get_dtype(None)
        base.header = parse_scan_header(base.header_raw)
        base.byte_offset += 4
        return base, _provenance("nanonispy2", "0.1.0")
    except ImportError:
        from nanonispy.read import NanonisFile, _parse_sxm_header

        base = object.__new__(NanonisFile)
        with _legacy_numpy_aliases(True):
            NanonisFile.__init__(base, str(path))
            base.set_data_format(None)
            base.header = _parse_sxm_header(base.header_raw)
        base.byte_offset += 4
        return base, _provenance("nanonispy", "1.1.0")


def _parser_class(kind: str) -> tuple[type[Any], ParserProvenance, bool]:
    class_name = {"sxm": "Scan", "3ds": "Grid", "dat": "Spec"}[kind]
    try:
        import nanonispy2

        return (
            getattr(nanonispy2, class_name),
            _provenance("nanonispy2", "0.1.0"),
            False,
        )
    except ImportError:
        try:
            from nanonispy import read
        except ImportError as exc:
            raise ImportError(
                "Nanonis readers require nanonispy; install qcodes-nanonis "
                "with its declared dependencies"
            ) from exc
        return (
            getattr(read, class_name),
            _provenance("nanonispy", "1.1.0"),
            True,
        )


def _provenance(distribution: str, fallback: str) -> ParserProvenance:
    try:
        installed = version(distribution)
    except PackageNotFoundError:
        installed = fallback
    return ParserProvenance(distribution, installed)


@contextmanager
def _legacy_numpy_aliases(enabled: bool) -> Iterator[None]:
    """Keep nanonispy 1.1 usable with NumPy 2 without leaking aliases."""
    if not enabled:
        yield
        return
    missing = {name: value for name, value in (("float", float), ("int", int))
               if name not in np.__dict__}
    try:
        for name, value in missing.items():
            setattr(np, name, value)
        yield
    finally:
        for name in missing:
            delattr(np, name)
