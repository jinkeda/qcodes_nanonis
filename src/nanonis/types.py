"""Hardware-free shared value types."""

from enum import Enum


class NaNPolicy(Enum):
    """Policy for non-finite values in acquired or file-backed data."""

    ALLOW = "allow"
    WARN = "warn"
    RAISE = "raise"


__all__ = ["NaNPolicy"]
