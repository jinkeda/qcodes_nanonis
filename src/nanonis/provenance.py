"""Package provenance helpers shared across independent feature verticals."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


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


__all__ = ["software_provenance"]
