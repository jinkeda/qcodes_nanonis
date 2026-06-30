"""Acquire-first QCoDeS persistence for bias-spectroscopy results."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from qcodes.dataset.measurements import Measurement

from ..workflows.spectroscopy.result import BiasSpectroscopyResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisteredTrace:
    parameter_name: str
    label: str
    occurrence: int


@dataclass(frozen=True)
class RegisteredBiasSpectroscopy:
    sample_index_name: str
    voltage_name: str | None
    traces: tuple[RegisteredTrace, ...]


def create_bias_spectroscopy_measurement(
    experiment: Any,
    result: BiasSpectroscopyResult,
    *,
    station: Any = None,
    name: str = "bias spectroscopy",
) -> tuple[Measurement, RegisteredBiasSpectroscopy]:
    """Create and register a QCoDeS measurement from an acquired result."""
    measurement = Measurement(exp=experiment, station=station, name=name)
    registered = register_bias_spectroscopy(measurement, result)
    return measurement, registered


def register_bias_spectroscopy(
    measurement: Any, result: BiasSpectroscopyResult
) -> RegisteredBiasSpectroscopy:
    """Register setpoint and trace array parameters before ``measurement.run``."""
    sample_index_name = "sample_index"
    measurement.register_custom_parameter(
        sample_index_name,
        label="Sample index",
        unit="",
        paramtype="array",
    )

    effective = result.effective_settings
    voltage_name: str | None = None
    if not effective.include_backward and result.data_columns == effective.points:
        voltage_name = "configured_voltage"
        measurement.register_custom_parameter(
            voltage_name,
            label="Configured sweep voltage",
            unit="V",
            paramtype="array",
        )
    elif effective.include_backward:
        logger.warning(
            "Backward trace directions are not characterized; registering only "
            "sample_index as a setpoint"
        )

    used = {sample_index_name, "configured_voltage"}
    traces = []
    setpoints = (
        (sample_index_name, voltage_name)
        if voltage_name is not None
        else (sample_index_name,)
    )
    for trace in result.traces():
        base = _sanitize_identifier(trace.name)
        parameter_name = _unique_identifier(base, used)
        used.add(parameter_name)
        measurement.register_custom_parameter(
            parameter_name,
            label=trace.name,
            unit=_unit_from_label(trace.name),
            setpoints=setpoints,
            paramtype="array",
        )
        traces.append(
            RegisteredTrace(parameter_name, trace.name, trace.occurrence)
        )
    return RegisteredBiasSpectroscopy(
        sample_index_name, voltage_name, tuple(traces)
    )


def add_bias_spectroscopy_result(
    datasaver: Any,
    registered: RegisteredBiasSpectroscopy,
    result: BiasSpectroscopyResult,
) -> None:
    """Insert one complete normalized result and its acquisition metadata."""
    if len(registered.traces) != len(result.channel_names):
        raise ValueError("registered trace schema does not match result channels")
    pairs: list[tuple[str, Any]] = [
        (registered.sample_index_name, np.arange(result.data_columns, dtype=int))
    ]
    if registered.voltage_name is not None:
        pairs.append((registered.voltage_name, result.forward_axis().values))
    pairs.extend(
        (registration.parameter_name, trace.values)
        for registration, trace in zip(registered.traces, result.traces())
    )
    datasaver.add_result(*pairs)

    metadata = {
        "acquisition_started_at": result.acquisition_started_at.isoformat(),
        "acquisition_finished_at": result.acquisition_finished_at.isoformat(),
        "acquisition_duration_s": result.acquisition_duration,
        "estimated_acquisition_duration_s": result.estimated_acquisition_duration,
        "acquisition_timeout_used_s": result.acquisition_timeout_used,
        "save_base_name": result.save_base_name,
        "saved_paths": json.dumps(result.saved_paths),
        "requested_config": json.dumps(asdict(result.requested_config)),
        "effective_settings": json.dumps(asdict(result.effective_settings)),
    }
    dataset = getattr(datasaver, "dataset", None)
    if dataset is None or not hasattr(dataset, "add_metadata"):
        raise TypeError("datasaver must expose dataset.add_metadata")
    for key, value in metadata.items():
        dataset.add_metadata(key, value)


def _sanitize_identifier(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    identifier = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    if not identifier:
        identifier = "trace"
    if identifier[0].isdigit():
        identifier = f"trace_{identifier}"
    return identifier


def _unique_identifier(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    occurrence = 2
    while f"{base}_{occurrence}" in used:
        occurrence += 1
    return f"{base}_{occurrence}"


def _unit_from_label(label: str) -> str:
    match = re.search(r"\(([^()]*)\)\s*(?:\[[^]]+\])?$", label)
    return match.group(1) if match else ""


__all__ = [
    "RegisteredBiasSpectroscopy",
    "RegisteredTrace",
    "add_bias_spectroscopy_result",
    "create_bias_spectroscopy_measurement",
    "register_bias_spectroscopy",
]
