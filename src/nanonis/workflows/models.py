"""Configuration, safety policy, and typed BiasSpectr module settings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from math import isfinite
from typing import Any, Callable, Mapping, TypeAlias

import numpy as np
import numpy.typing as npt

from .protocols import CommandClient


class BiasRestoreMode(Enum):
    DIRECT = "direct"
    STEPPED = "stepped"
    EXTERNAL = "external"


class ZeroCrossingPolicy(Enum):
    ALLOW = "allow"
    FORBID = "forbid"


@dataclass(frozen=True)
class BiasRampPolicy:
    max_step: float
    dwell_time: float
    zero_crossing_policy: ZeroCrossingPolicy

    def __post_init__(self) -> None:
        if not isfinite(self.max_step) or self.max_step <= 0:
            raise ValueError("max_step must be finite and > 0")
        if not isfinite(self.dwell_time) or self.dwell_time < 0:
            raise ValueError("dwell_time must be finite and >= 0")


ExternalBiasRestorer = Callable[[CommandClient, float], None]


@dataclass(frozen=True)
class TipRestorePolicy:
    """Vertical-neutral policy for restoring tunnel conditions."""

    bias_restore_mode: BiasRestoreMode
    bias_ramp: BiasRampPolicy | None
    allow_zero_crossing: bool
    feedback_off_during_restore: bool = True
    external_bias_restorer: ExternalBiasRestorer | None = None

    def __post_init__(self) -> None:
        if self.bias_restore_mode is BiasRestoreMode.STEPPED and self.bias_ramp is None:
            raise ValueError("STEPPED bias restoration requires bias_ramp")
        if (
            self.bias_restore_mode is BiasRestoreMode.EXTERNAL
            and self.external_bias_restorer is None
        ):
            raise ValueError("EXTERNAL bias restoration requires a callback")


@dataclass(frozen=True)
class BiasSpectroscopySafetyPolicy:
    max_abs_bias: float
    max_abs_z_offset: float
    min_slew_rate: float
    max_slew_rate: float
    bias_restore_mode: BiasRestoreMode
    bias_ramp: BiasRampPolicy | None
    allow_zero_crossing: bool
    feedback_off_during_restore: bool = True
    external_bias_restorer: ExternalBiasRestorer | None = None

    def __post_init__(self) -> None:
        positive = (self.max_abs_bias, self.max_abs_z_offset, self.min_slew_rate)
        if any(not isfinite(value) or value <= 0 for value in positive):
            raise ValueError("absolute limits and min_slew_rate must be finite and > 0")
        if not isfinite(self.max_slew_rate) or self.max_slew_rate < self.min_slew_rate:
            raise ValueError("max_slew_rate must be finite and >= min_slew_rate")
        self.tip  # validate the composed, shared policy

    @property
    def tip(self) -> TipRestorePolicy:
        """Return the shared tip-restoration portion of this policy."""
        return TipRestorePolicy(
            bias_restore_mode=self.bias_restore_mode,
            bias_ramp=self.bias_ramp,
            allow_zero_crossing=self.allow_zero_crossing,
            feedback_off_during_restore=self.feedback_off_during_restore,
            external_bias_restorer=self.external_bias_restorer,
        )


@dataclass(frozen=True)
class BiasSpectroscopyConfig:
    start_voltage: float
    stop_voltage: float
    points: int
    channel_indexes: tuple[int, ...]
    sweeps: int = 1
    include_backward: bool = False
    save_individual_sweeps: bool = False
    z_offset: float | None = None
    integration_time: float | None = None
    settling_time: float | None = None
    maximum_slew_rate: float | None = None
    save_base_name: str = ""
    acquisition_timeout: float | None = None
    recovery_timeout: float = 15.0
    status_poll_interval: float = 0.1
    restore_tip_state: bool = True
    restore_module_settings: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "channel_indexes", tuple(self.channel_indexes))
        if self.points < 2:
            raise ValueError("points must be >= 2")
        if self.sweeps < 1:
            raise ValueError("sweeps must be >= 1")
        if not self.channel_indexes:
            raise ValueError("need >= 1 channel")
        if len(set(self.channel_indexes)) != len(self.channel_indexes):
            raise ValueError("duplicate channel indexes")
        if any(index < 0 for index in self.channel_indexes):
            raise ValueError("channel index must be >= 0")
        if not (isfinite(self.start_voltage) and isfinite(self.stop_voltage)):
            raise ValueError("non-finite voltage")
        if self.start_voltage == self.stop_voltage:
            raise ValueError("start_voltage == stop_voltage")
        for value in (
            self.integration_time,
            self.settling_time,
            self.maximum_slew_rate,
        ):
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError("timing/slew overrides must be finite and > 0")
        if self.z_offset is not None and not isfinite(self.z_offset):
            raise ValueError("z_offset must be finite when provided")
        if self.acquisition_timeout is not None and (
            not isfinite(self.acquisition_timeout) or self.acquisition_timeout <= 0
        ):
            raise ValueError("acquisition_timeout must be finite and > 0 when provided")
        if not isfinite(self.recovery_timeout) or self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be finite and > 0")
        if not isfinite(self.status_poll_interval) or self.status_poll_interval <= 0:
            raise ValueError("status_poll_interval must be finite and > 0")
        if self.status_poll_interval > self.recovery_timeout:
            raise ValueError("status_poll_interval cannot exceed recovery_timeout")
        if not isinstance(self.save_base_name, str):
            raise TypeError("save_base_name must be a string")


@dataclass(frozen=True)
class BiasSpectroscopyTiming:
    z_averaging_time: float
    z_offset: float
    initial_settling_time: float
    maximum_slew_rate: float
    settling_time: float
    integration_time: float
    end_settling_time: float
    z_control_time: float

    @classmethod
    def from_response(cls, response: Mapping[str, Any]) -> "BiasSpectroscopyTiming":
        return cls(
            float(response["z_averaging_time_s"]),
            float(response["z_offset_m"]),
            float(response["initial_settling_time_s"]),
            float(response["maximum_slew_rate_v_s"]),
            float(response["settling_time_s"]),
            float(response.get("integration_time_s", response.get("integration_time"))),
            float(response["end_settling_time_s"]),
            float(response["z_control_time_s"]),
        )

    def setter_args(self, *, z_offset: float | None = None) -> tuple[float, ...]:
        return (
            self.z_averaging_time,
            self.z_offset if z_offset is None else z_offset,
            self.initial_settling_time,
            self.maximum_slew_rate,
            self.settling_time,
            self.integration_time,
            self.end_settling_time,
            self.z_control_time,
        )


@dataclass(frozen=True)
class BiasSpectroscopyAdvanced:
    reset_bias: bool
    z_controller_hold: bool
    record_final_z: bool
    lockin_run: bool

    @classmethod
    def from_response(cls, response: Mapping[str, Any]) -> "BiasSpectroscopyAdvanced":
        return cls(
            bool(response["reset_bias"]),
            bool(response["z_controller_hold"]),
            bool(response["record_final_z"]),
            bool(response["lockin_run"]),
        )

    def setter_args(self) -> tuple[int, int, int, int]:
        return (
            1 if self.reset_bias else 2,
            1 if self.z_controller_hold else 2,
            1 if self.record_final_z else 2,
            1 if self.lockin_run else 2,
        )


@dataclass(frozen=True)
class BiasSpectroscopySettings:
    channels: tuple[int, ...]
    save_all: bool
    sweeps: int
    include_backward: bool
    points: int
    autosave: bool
    show_save_dialog: bool
    timing: BiasSpectroscopyTiming
    advanced: BiasSpectroscopyAdvanced
    limits: tuple[float, float]
    parameter_names: tuple[str, ...] = ()
    fixed_parameter_names: tuple[str, ...] = ()

    @classmethod
    def snapshot(cls, client: CommandClient) -> "BiasSpectroscopySettings":
        channels = _mapping(client.send("BiasSpectr.ChsGet"), "ChsGet")
        props = _mapping(client.send("BiasSpectr.PropsGet"), "PropsGet")
        limits = _mapping(client.send("BiasSpectr.LimitsGet"), "LimitsGet")
        timing = _mapping(client.send("BiasSpectr.TimingGet"), "TimingGet")
        advanced = _mapping(client.send("BiasSpectr.AdvPropsGet"), "AdvPropsGet")
        return cls(
            channels=tuple(int(value) for value in channels["channel_indexes"]),
            save_all=bool(props["save_all"]),
            sweeps=int(props["num_sweeps"]),
            include_backward=bool(props["backward_sweep"]),
            points=int(props["num_points"]),
            autosave=bool(props["autosave"]),
            show_save_dialog=bool(props["show_save_dialog"]),
            timing=BiasSpectroscopyTiming.from_response(timing),
            advanced=BiasSpectroscopyAdvanced.from_response(advanced),
            limits=(float(limits["start_value_v"]), float(limits["end_value_v"])),
            parameter_names=tuple(str(v) for v in props.get("parameters", ())),
            fixed_parameter_names=tuple(
                str(v) for v in props.get("fixed_parameters", ())
            ),
        )

    def patch(self, config: BiasSpectroscopyConfig) -> "BiasSpectroscopySettings":
        timing = replace(
            self.timing,
            z_offset=(
                self.timing.z_offset if config.z_offset is None else config.z_offset
            ),
            integration_time=(
                self.timing.integration_time
                if config.integration_time is None
                else config.integration_time
            ),
            settling_time=(
                self.timing.settling_time
                if config.settling_time is None
                else config.settling_time
            ),
            maximum_slew_rate=(
                self.timing.maximum_slew_rate
                if config.maximum_slew_rate is None
                else config.maximum_slew_rate
            ),
        )
        return replace(
            self,
            channels=config.channel_indexes,
            save_all=config.save_individual_sweeps,
            sweeps=config.sweeps,
            include_backward=config.include_backward,
            points=config.points,
            timing=timing,
            limits=(config.start_voltage, config.stop_voltage),
        )

    def apply(self, client: CommandClient, *, include_advanced: bool = False) -> None:
        z_offset = self.timing.z_offset
        client.send("BiasSpectr.ChsSet", len(self.channels), self.channels)
        client.send(
            "BiasSpectr.PropsSet",
            _wire_bool(self.save_all),
            self.sweeps,
            _wire_bool(self.include_backward),
            self.points,
            z_offset,
            _wire_bool(self.autosave),
            _wire_bool(self.show_save_dialog),
        )
        client.send("BiasSpectr.LimitsSet", *self.limits)
        client.send("BiasSpectr.TimingSet", *self.timing.setter_args())
        if include_advanced:
            client.send("BiasSpectr.AdvPropsSet", *self.advanced.setter_args())

    def restore(self, client: CommandClient) -> dict[str, BaseException]:
        """Restore every module field in the lab-defined order, best effort."""
        failures: dict[str, BaseException] = {}
        operations = (
            ("channels", "BiasSpectr.ChsSet", (len(self.channels), self.channels)),
            ("limits", "BiasSpectr.LimitsSet", self.limits),
            ("timing", "BiasSpectr.TimingSet", self.timing.setter_args()),
            (
                "properties",
                "BiasSpectr.PropsSet",
                (
                    _wire_bool(self.save_all),
                    self.sweeps,
                    _wire_bool(self.include_backward),
                    self.points,
                    self.timing.z_offset,
                    _wire_bool(self.autosave),
                    _wire_bool(self.show_save_dialog),
                ),
            ),
            ("advanced", "BiasSpectr.AdvPropsSet", self.advanced.setter_args()),
        )
        for field, command, args in operations:
            try:
                client.send(command, *args)
            except BaseException as exc:
                failures[field] = exc
        return failures


FloatArray: TypeAlias = npt.NDArray[np.float64]


@dataclass(frozen=True)
class SweepAxis:
    values: FloatArray
    unit: str = "V"
    source: str = "configured sweep limits"
    direction: str = "forward"

    def __post_init__(self) -> None:
        values = np.array(self.values, dtype=np.float64, copy=True)
        values.setflags(write=False)
        object.__setattr__(self, "values", values)
        if self.direction not in {"forward", "backward"}:
            raise ValueError("direction must be 'forward' or 'backward'")


def _mapping(value: Any, command: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"BiasSpectr.{command} must return a mapping")
    return value


def _wire_bool(value: bool) -> int:
    return 1 if value else 2
