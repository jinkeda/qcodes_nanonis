"""Transactional bias-spectroscopy orchestration."""

from __future__ import annotations

import logging
import math
import re
import time
from datetime import datetime, timezone
from typing import Any, Mapping

from nanonis.protocol import (
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)

from ..errors import (
    NonFiniteSpectroscopyDataError,
    RecoveryError,
    SafetyPreflightError,
)
from ..models import (
    BiasSpectroscopyConfig,
    BiasSpectroscopySafetyPolicy,
    BiasSpectroscopySettings,
)
from ..protocols import CommandClient, RecoverableCommandClient
from .result import (
    BiasSpectroscopyResult,
    NaNPolicy,
    normalize_bias_spectroscopy_response,
)
from ..state import (
    RecoveryReport,
    RestorationTransaction,
    TipState,
    recover_bias_spectroscopy,
)

logger = logging.getLogger(__name__)
RECOVERABLE_TRANSPORT_ERRORS = (
    NanonisTimeoutError,
    NanonisConnectionError,
    NanonisProtocolError,
)


class BiasSpectroscopyWorkflow:
    def __init__(
        self,
        client: CommandClient,
        *,
        safety_policy: BiasSpectroscopySafetyPolicy,
        nan_policy: NaNPolicy = NaNPolicy.WARN,
    ) -> None:
        self._client = client
        self._safety = safety_policy
        self._nan_policy = nan_policy

    def run(
        self,
        config: BiasSpectroscopyConfig,
        *,
        unsafe_skip_preflight: bool = False,
    ) -> BiasSpectroscopyResult:
        if not isinstance(config, BiasSpectroscopyConfig):
            raise TypeError("config must be BiasSpectroscopyConfig")
        _validate_requested_safety(config, self._safety)
        if not unsafe_skip_preflight:
            preflight_bias_spectroscopy(self._client, config, self._safety)

        result: BiasSpectroscopyResult | None = None
        with RestorationTransaction(self._client) as tx:
            if config.restore_tip_state:
                tip = TipState.snapshot(self._client)
                tx.preserve(
                    "tip",
                    tip,
                    restorer=lambda state: state.restore(self._client, self._safety),
                )

            self._client.send("BiasSpectr.Open")
            original = BiasSpectroscopySettings.snapshot(self._client)
            tx.preserve(
                "bias_spectroscopy",
                original,
                restorer=lambda state: state.restore(self._client),
                enabled=config.restore_module_settings,
            )
            desired = original.patch(config)
            _validate_effective_safety(desired, self._safety)
            desired.apply(self._client)
            effective = BiasSpectroscopySettings.snapshot(self._client)
            _validate_effective_safety(effective, self._safety)

            estimate = estimate_acquisition_duration(effective)
            acquisition_timeout = (
                config.acquisition_timeout
                if config.acquisition_timeout is not None
                else estimate * 1.5 + 5.0
            )
            started_at = datetime.now(timezone.utc)
            started_monotonic = time.monotonic()
            try:
                response = self._client.send(
                    "BiasSpectr.Start",
                    1,
                    config.save_base_name,
                    timeout=acquisition_timeout,
                )
            except RECOVERABLE_TRANSPORT_ERRORS + (KeyboardInterrupt,) as exc:
                report = self._recover(config)
                tx.record_recovery(report, origin=exc)
                raise
            finished_monotonic = time.monotonic()
            finished_at = datetime.now(timezone.utc)

            if not isinstance(response, Mapping):
                raise TypeError("BiasSpectr.Start must return a mapping")
            try:
                result = normalize_bias_spectroscopy_response(
                    response,
                    config=config,
                    effective=effective,
                    acquisition_started_at=started_at,
                    acquisition_finished_at=finished_at,
                    acquisition_duration=finished_monotonic - started_monotonic,
                    estimated_acquisition_duration=estimate,
                    acquisition_timeout_used=acquisition_timeout,
                    nan_policy=self._nan_policy,
                )
            except NonFiniteSpectroscopyDataError as exc:
                tx.attach_result(exc.result)
                raise
            tx.attach_result(result)

        if result is None:  # defensive; every successful path assigns it above
            raise RuntimeError("BiasSpectr workflow completed without a result")
        return result

    def _recover(self, config: BiasSpectroscopyConfig) -> RecoveryReport:
        if isinstance(self._client, RecoverableCommandClient):
            return recover_bias_spectroscopy(
                self._client,
                timeout=config.recovery_timeout,
                poll_interval=config.status_poll_interval,
            )
        return RecoveryReport(
            False,
            None,
            (RecoveryError("command client does not support reconnect"),),
        )


def estimate_acquisition_duration(settings: BiasSpectroscopySettings) -> float:
    timing = settings.timing
    timing_is_incomplete = any(
        not math.isfinite(value) or value < 0
        for value in (timing.integration_time, timing.settling_time)
    )
    point_time = _nonnegative_timing(
        timing.integration_time, "integration_time"
    ) + _nonnegative_timing(timing.settling_time, "settling_time")
    sampling_time = settings.points * point_time
    if math.isfinite(timing.maximum_slew_rate) and timing.maximum_slew_rate > 0:
        slew_time = abs(settings.limits[1] - settings.limits[0]) / timing.maximum_slew_rate
    else:
        slew_time = 0.0
        timing_is_incomplete = True
        logger.warning(
            "Cannot estimate slew-limited duration from maximum_slew_rate=%r",
            timing.maximum_slew_rate,
        )
    one_direction = max(sampling_time, slew_time)
    directions = 2 if settings.include_backward else 1
    estimate = (
        _nonnegative_timing(timing.initial_settling_time, "initial_settling_time")
        + _nonnegative_timing(timing.z_control_time, "z_control_time")
        + _nonnegative_timing(timing.z_averaging_time, "z_averaging_time")
        + settings.sweeps * directions * one_direction
        + _nonnegative_timing(timing.end_settling_time, "end_settling_time")
    )
    estimate = max(0.0, float(estimate))
    if timing_is_incomplete:
        logger.warning(
            "Using a 60 s fallback acquisition estimate because effective "
            "timing is incomplete"
        )
        estimate = max(estimate, 60.0)
    return estimate


def _nonnegative_timing(value: float, name: str) -> float:
    if math.isfinite(value) and value >= 0:
        return value
    logger.warning("Ignoring invalid %s=%r while estimating acquisition", name, value)
    return 0.0


def preflight_bias_spectroscopy(
    client: CommandClient,
    config: BiasSpectroscopyConfig,
    policy: BiasSpectroscopySafetyPolicy,
) -> None:
    range_response = client.send("Bias.RangeGet")
    if not isinstance(range_response, Mapping):
        raise SafetyPreflightError("Bias.RangeGet did not return range metadata")
    try:
        ranges = tuple(str(value) for value in range_response["bias_ranges"])
        active_index = int(range_response["bias_range_index"])
        active_range = ranges[active_index]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise SafetyPreflightError(f"invalid active bias-range response: {exc}") from exc
    if active_range.strip().casefold() == "not switchable":
        # Fixed-range controllers do not expose a numeric range through
        # Bias.RangeGet. Fall back to the stricter, rig-approved policy bound;
        # never infer the physical range from the GUI or a hard-coded value.
        lower, upper = -policy.max_abs_bias, policy.max_abs_bias
        logger.warning(
            "Bias.RangeGet returned 'Not switchable'; using the safety-policy "
            "bound [%g, %g] V for preflight",
            lower,
            upper,
        )
    else:
        lower, upper = parse_bias_range(active_range)
    for label, voltage in (
        ("start_voltage", config.start_voltage),
        ("stop_voltage", config.stop_voltage),
    ):
        if not lower <= voltage <= upper:
            raise SafetyPreflightError(
                f"{label}={voltage:g} V is outside active range {active_range!r}"
            )

    signal_response = client.send("Signals.NamesGet")
    if not isinstance(signal_response, Mapping):
        raise SafetyPreflightError("Signals.NamesGet did not return signal metadata")
    try:
        names = tuple(signal_response["signals_names"])
    except (KeyError, TypeError) as exc:
        raise SafetyPreflightError(f"invalid signal-name response: {exc}") from exc
    invalid = [index for index in config.channel_indexes if index >= len(names)]
    if invalid:
        raise SafetyPreflightError(
            f"channel indexes {invalid} do not exist; controller returned {len(names)} signals"
        )

    status = client.send("BiasSpectr.StatusGet")
    if isinstance(status, Mapping):
        status = status["status"]
    if int(status) != 0:
        raise SafetyPreflightError("Bias spectroscopy is already running")


def parse_bias_range(description: str) -> tuple[float, float]:
    normalized = description.strip().replace("−", "-").replace("–", "-")
    if not re.search(r"\b(?:m?v)\b", normalized, re.IGNORECASE):
        raise SafetyPreflightError(
            f"unsupported bias-range description {description!r}: missing V/mV unit"
        )
    scale = 1e-3 if re.search(r"\bmv\b", normalized, re.IGNORECASE) else 1.0
    symmetric = "±" in normalized or "+/-" in normalized or "+-" in normalized
    number_text = re.sub(r"\s+-\s+", " ", normalized)
    numbers = [
        float(value)
        for value in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", number_text)
    ]
    if symmetric and len(numbers) == 1:
        limit = abs(numbers[0]) * scale
        return -limit, limit
    if len(numbers) == 1:
        limit = abs(numbers[0]) * scale
        return -limit, limit
    if len(numbers) == 2:
        lower, upper = sorted(value * scale for value in numbers)
        if lower == upper:
            raise SafetyPreflightError(f"zero-width bias range {description!r}")
        return lower, upper
    raise SafetyPreflightError(f"unsupported bias-range description {description!r}")


def _validate_requested_safety(
    config: BiasSpectroscopyConfig, policy: BiasSpectroscopySafetyPolicy
) -> None:
    if max(abs(config.start_voltage), abs(config.stop_voltage)) > policy.max_abs_bias:
        raise SafetyPreflightError(
            f"requested bias exceeds policy limit ±{policy.max_abs_bias:g} V"
        )
    if config.z_offset is not None and abs(config.z_offset) > policy.max_abs_z_offset:
        raise SafetyPreflightError(
            f"requested z_offset exceeds policy limit ±{policy.max_abs_z_offset:g} m"
        )
    if config.maximum_slew_rate is not None and not (
        policy.min_slew_rate
        <= config.maximum_slew_rate
        <= policy.max_slew_rate
    ):
        raise SafetyPreflightError("requested maximum_slew_rate is outside policy bounds")


def _validate_effective_safety(
    settings: BiasSpectroscopySettings, policy: BiasSpectroscopySafetyPolicy
) -> None:
    if max(abs(value) for value in settings.limits) > policy.max_abs_bias:
        raise SafetyPreflightError("effective bias limits exceed the safety policy")
    if abs(settings.timing.z_offset) > policy.max_abs_z_offset:
        raise SafetyPreflightError("effective z_offset exceeds the safety policy")
    if not (
        policy.min_slew_rate
        <= settings.timing.maximum_slew_rate
        <= policy.max_slew_rate
    ):
        raise SafetyPreflightError("effective maximum_slew_rate is outside policy bounds")


def bias_spectroscopy(
    nanonis: Any,
    *,
    safety_policy: BiasSpectroscopySafetyPolicy,
    nan_policy: NaNPolicy = NaNPolicy.WARN,
) -> BiasSpectroscopyWorkflow:
    """Build a workflow from a NanonisInstrument or a command client."""
    client = getattr(nanonis, "controller", nanonis)
    return BiasSpectroscopyWorkflow(
        client, safety_policy=safety_policy, nan_policy=nan_policy
    )
