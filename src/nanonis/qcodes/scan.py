"""Deferred QCoDeS persistence seam for scan results."""

from __future__ import annotations

from typing import Any

from nanonis.workflows.scan import ScanResult


def register_scan_result(
    experiment: Any, result: ScanResult, *, station: Any = None
) -> Any:
    """Deferred. Register a ScanResult's schema with QCoDeS."""
    raise NotImplementedError(
        "scan QCoDeS persistence is deferred; see scan_workflow_plan.md"
    )


def add_scan_result(datasaver: Any, registered: Any, result: ScanResult) -> None:
    """Deferred. Insert a ScanResult into a QCoDeS run."""
    raise NotImplementedError(
        "scan QCoDeS persistence is deferred; see scan_workflow_plan.md"
    )
