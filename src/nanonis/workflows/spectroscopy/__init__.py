"""Bias-spectroscopy workflow vertical.

The first end-to-end measurement workflow. Built on the shared workflow toolkit
(``protocols``, ``errors``, ``state``, ``models`` one level up); other
spectroscopy types can be added alongside ``bias_spectroscopy`` here.
"""

from .bias_spectroscopy import (
    RECOVERABLE_TRANSPORT_ERRORS,
    BiasSpectroscopyWorkflow,
    bias_spectroscopy,
    estimate_acquisition_duration,
    parse_bias_range,
    preflight_bias_spectroscopy,
)
from .result import (
    BiasSpectroscopyResult,
    NaNPolicy,
    NonFiniteDiagnostics,
    SpectroscopyParameter,
    SpectroscopyTrace,
    apply_nan_policy,
    inspect_non_finite_data,
    normalize_bias_spectroscopy_response,
)

__all__ = [
    "RECOVERABLE_TRANSPORT_ERRORS",
    "BiasSpectroscopyResult",
    "BiasSpectroscopyWorkflow",
    "NaNPolicy",
    "NonFiniteDiagnostics",
    "SpectroscopyParameter",
    "SpectroscopyTrace",
    "apply_nan_policy",
    "bias_spectroscopy",
    "estimate_acquisition_duration",
    "inspect_non_finite_data",
    "normalize_bias_spectroscopy_response",
    "parse_bias_range",
    "preflight_bias_spectroscopy",
]
