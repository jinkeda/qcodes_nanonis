"""Workflow-specific exceptions with recoverable context."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


class WorkflowError(Exception):
    """Base class for orchestration failures."""


class SpectroscopyResponseError(WorkflowError):
    """A fully received BiasSpectr response has inconsistent semantics."""


class ScanResponseError(WorkflowError):
    """A fully received scan response has inconsistent semantics."""


class ScanTimeoutError(WorkflowError):
    """Nanonis did not complete a scan inside its controller-side timeout."""


class NonFiniteScanDataError(ScanResponseError):
    """Raised by NaNPolicy.RAISE while retaining the normalized scan result."""

    def __init__(self, result: Any, diagnostics: Any) -> None:
        self.result = result
        self.diagnostics = diagnostics
        super().__init__(
            f"scan data contains {diagnostics.nan_count} NaN and "
            f"{diagnostics.inf_count} infinite values"
        )


class SafetyPreflightError(WorkflowError):
    """A live or configured safety check failed before acquisition."""


class RecoveryError(WorkflowError):
    """Transport recovery or stop confirmation did not complete."""

    def __init__(self, message: str, errors: tuple[BaseException, ...] = ()) -> None:
        self.errors = errors
        super().__init__(message)


class StateRestorationError(WorkflowError):
    """Aggregate recovery/restoration failure without losing acquired data."""

    def __init__(
        self,
        *,
        original_error: BaseException | None,
        failures: Mapping[str, BaseException],
        recovery_error: BaseException | None = None,
        result: Any = None,
    ) -> None:
        self.original_error = original_error
        self.recovery_error = recovery_error
        self.failures = MappingProxyType(dict(failures))
        self.result = result
        parts = []
        if recovery_error is not None:
            parts.append(f"recovery failed: {recovery_error}")
        if failures:
            parts.append("restoration failures: " + ", ".join(failures))
        if not parts:
            parts.append("state restoration could not be completed")
        super().__init__("; ".join(parts))


class NonFiniteSpectroscopyDataError(WorkflowError):
    """Raised by NaNPolicy.RAISE while retaining the normalized result."""

    def __init__(self, result: Any, diagnostics: Any) -> None:
        self.result = result
        self.diagnostics = diagnostics
        super().__init__(
            f"spectroscopy data contains {diagnostics.nan_count} NaN and "
            f"{diagnostics.inf_count} infinite values"
        )

