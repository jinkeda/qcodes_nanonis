"""Transactional, one-frame Nanonis scan workflow."""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timezone
from typing import Any, Mapping

from ..errors import (
    NonFiniteScanDataError,
    RecoveryError,
    SafetyPreflightError,
    ScanResponseError,
    ScanTimeoutError,
    WorkflowError,
)
from ..protocols import CommandClient, RecoverableCommandClient
from ..spectroscopy.result import NaNPolicy
from ..state import RecoveryReport, RestorationTransaction, TipState, recover_module
from .models import ScanConfig, ScanSafetyPolicy, ScanSettings
from .result import ScanResult, normalize_scan, normalize_scan_images

logger = logging.getLogger(__name__)

ACTION_START = 0
ACTION_STOP = 1
DIRECTION_DOWN = 0
DIRECTION_UP = 1
STATUS_IDLE = 0
WAIT_COMPLETED = 0
WAIT_TIMED_OUT = 1
DATA_BACKWARD = 0
DATA_FORWARD = 1

POSITIONING_MARGIN_SECONDS = 1.0
NANONIS_TIMEOUT_MARGIN_MS = 5_000
MAX_NANONIS_TIMEOUT_MS = 2_147_483_647


class ScanWorkflow:
    def __init__(
        self,
        client: CommandClient,
        *,
        safety_policy: ScanSafetyPolicy,
        nan_policy: NaNPolicy = NaNPolicy.WARN,
    ) -> None:
        self._client = client
        self._safety = safety_policy
        self._nan_policy = nan_policy

    def run(
        self,
        config: ScanConfig,
        *,
        unsafe_skip_preflight: bool = False,
    ) -> ScanResult:
        if not isinstance(config, ScanConfig):
            raise TypeError("config must be ScanConfig")
        _validate_requested_safety(config, self._safety)
        if config.restore_tip_state and self._safety.tip is None:
            raise SafetyPreflightError(
                "restore_tip_state requires ScanSafetyPolicy.tip"
            )
        if not unsafe_skip_preflight:
            preflight_scan(self._client, config, self._safety)

        result: ScanResult | None = None
        with RestorationTransaction(self._client) as tx:
            if config.restore_tip_state:
                tip = TipState.snapshot(self._client)
                policy = self._safety.tip
                if policy is None:  # guarded before any I/O
                    raise RuntimeError("missing tip restoration policy")
                tx.preserve(
                    "tip",
                    tip,
                    restorer=lambda state: state.restore(self._client, policy),
                )

            original = ScanSettings.snapshot(self._client)
            desired = original.patch(config)
            _validate_effective_safety(desired, self._safety)
            _validate_timeout_budget(config, desired)
            tx.preserve(
                "scan",
                original,
                restorer=lambda state: state.restore(self._client),
                enabled=config.restore_state,
            )
            failures = desired.apply(self._client)
            if failures:
                raise WorkflowError(
                    "scan configuration failed: "
                    + ", ".join(
                        f"{field}: {error}" for field, error in failures.items()
                    )
                )
            effective = ScanSettings.snapshot(self._client)
            _validate_effective_safety(effective, self._safety)

            estimate = estimate_scan_duration(effective)
            controller_timeout_ms = nanonis_timeout_ms(config, effective, estimate=estimate)
            acquisition_timeout = resolve_acquisition_timeout(
                config, effective, controller_timeout_ms=controller_timeout_ms, estimate=estimate
            )
            started_at = datetime.now(timezone.utc)
            started_monotonic = time.monotonic()
            start_attempted = False
            completed = False
            try:
                start_attempted = True
                self._client.send(
                    "Scan.Action",
                    ACTION_START,
                    DIRECTION_UP if config.direction == "up" else DIRECTION_DOWN,
                )
                wait = self._client.send(
                    "Scan.WaitEndOfScan",
                    controller_timeout_ms,
                    timeout=acquisition_timeout,
                )
                if not isinstance(wait, Mapping):
                    raise ScanResponseError("Scan.WaitEndOfScan must return a mapping")
                try:
                    timeout_status = int(wait["timeout_status"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ScanResponseError(
                        f"invalid Scan.WaitEndOfScan timeout status: {exc}"
                    ) from exc
                if timeout_status == WAIT_TIMED_OUT:
                    raise ScanTimeoutError(
                        f"scan exceeded Nanonis timeout {controller_timeout_ms} ms"
                    )
                if timeout_status != WAIT_COMPLETED:
                    raise ScanResponseError(
                        f"unknown WaitEndOfScan timeout status {timeout_status}"
                    )
                saved_path = str(wait.get("file_path", ""))
                completed = True
            except BaseException as exc:
                if start_attempted and not completed:
                    tx.record_recovery(self._recover(config), origin=exc)
                raise
            finished_monotonic = time.monotonic()
            finished_at = datetime.now(timezone.utc)

            images = ()
            if config.grab_data:
                images = grab_frame(self._client, effective, config)
            try:
                result = normalize_scan(
                    images,
                    saved_path=saved_path,
                    config=config,
                    effective=effective,
                    acquisition_started_at=started_at,
                    acquisition_finished_at=finished_at,
                    acquisition_duration=finished_monotonic - started_monotonic,
                    estimated_acquisition_duration=estimate,
                    acquisition_timeout_used=acquisition_timeout,
                    nan_policy=self._nan_policy,
                )
            except NonFiniteScanDataError as exc:
                tx.attach_result(exc.result)
                raise
            tx.attach_result(result)

        if result is None:
            raise RuntimeError("scan workflow completed without a result")
        return result

    def _recover(self, config: ScanConfig) -> RecoveryReport:
        if isinstance(self._client, RecoverableCommandClient):
            return recover_scan(
                self._client,
                timeout=config.recovery_timeout,
                poll_interval=config.status_poll_interval,
            )
        return RecoveryReport(
            False,
            None,
            (RecoveryError("command client does not support reconnect"),),
        )


def recover_scan(
    client: RecoverableCommandClient,
    *,
    timeout: float,
    poll_interval: float = 0.1,
) -> RecoveryReport:
    return recover_module(
        client,
        # Scan.Action ignores its direction argument for Stop; the protocol still
        # requires a uint32 placeholder.
        stop=lambda value: value.send("Scan.Action", ACTION_STOP, 0),
        status_stopped=_scan_status_stopped,
        timeout=timeout,
        poll_interval=poll_interval,
    )


def _scan_status_stopped(client: CommandClient) -> bool:
    return _scan_status_value(client.send("Scan.StatusGet")) == STATUS_IDLE


def _scan_status_value(response: Any) -> int:
    if isinstance(response, Mapping):
        try:
            response = response["scan_status"]
        except KeyError as exc:
            raise ScanResponseError(
                "Scan.StatusGet response is missing 'scan_status'"
            ) from exc
    try:
        status = int(response)
    except (TypeError, ValueError) as exc:
        raise ScanResponseError(
            f"invalid Scan.StatusGet response {response!r}"
        ) from exc
    if status not in (0, 1):
        raise ScanResponseError(f"invalid Scan.StatusGet status {status}")
    return status


def estimate_scan_duration(settings: ScanSettings) -> float:
    """Estimate a complete forward-plus-backward raster."""
    forward = settings.speed.forward_time_per_line
    backward = settings.speed.backward_time_per_line
    if any(not math.isfinite(value) or value <= 0 for value in (forward, backward)):
        logger.warning(
            "Using a 60 s fallback scan estimate because line timing is incomplete"
        )
        return 60.0
    return max(
        0.0,
        settings.lines * (forward + backward) + POSITIONING_MARGIN_SECONDS,
    )


def nanonis_timeout_ms(
    config: ScanConfig,
    effective: ScanSettings,
    *,
    estimate: float | None = None,
) -> int:
    del config  # reserved for future controller-timeout policy overrides
    duration = estimate_scan_duration(effective) if estimate is None else estimate
    return min(
        MAX_NANONIS_TIMEOUT_MS,
        max(1, math.ceil(duration * 1000 + NANONIS_TIMEOUT_MARGIN_MS)),
    )


def resolve_acquisition_timeout(
    config: ScanConfig,
    effective: ScanSettings,
    *,
    controller_timeout_ms: int | None = None,
    estimate: float | None = None,
) -> float:
    duration = estimate_scan_duration(effective) if estimate is None else estimate
    timeout_ms = (
        nanonis_timeout_ms(config, effective, estimate=duration)
        if controller_timeout_ms is None
        else controller_timeout_ms
    )
    minimum = max(duration, timeout_ms / 1000)
    if config.acquisition_timeout is None:
        return minimum * 1.5 + 5.0
    if config.acquisition_timeout <= timeout_ms / 1000:
        raise SafetyPreflightError(
            "acquisition_timeout must exceed the Nanonis controller-side timeout"
        )
    return config.acquisition_timeout


def grab_frame(
    client: CommandClient,
    effective: ScanSettings,
    config: ScanConfig,
):
    responses = []
    for channel_index in config.channel_indexes:
        for direction in config.data_directions:
            response = client.send(
                "Scan.FrameDataGrab",
                channel_index,
                DATA_FORWARD if direction == "forward" else DATA_BACKWARD,
            )
            if not isinstance(response, Mapping):
                raise ScanResponseError("Scan.FrameDataGrab must return a mapping")
            rows = int(response.get("scan_data_rows", -1))
            columns = int(response.get("scan_data_columns", -1))
            if rows != effective.lines or columns != effective.pixels:
                logger.warning(
                    "FrameDataGrab returned (%d, %d), expected (%d, %d); "
                    "preserving raw data",
                    rows,
                    columns,
                    effective.lines,
                    effective.pixels,
                )
            responses.append((channel_index, direction, response))
    return normalize_scan_images(responses)


def preflight_scan(
    client: CommandClient,
    config: ScanConfig,
    policy: ScanSafetyPolicy,
) -> None:
    range_response = client.send("Piezo.RangeGet")
    if not isinstance(range_response, Mapping):
        raise SafetyPreflightError("Piezo.RangeGet did not return range metadata")
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

    current = ScanSettings.snapshot(client)
    desired = current.patch(config)
    _validate_effective_safety(desired, policy)
    _validate_timeout_budget(config, desired)
    try:
        range_x = float(range_response["range_x_m"])
        range_y = float(range_response["range_y_m"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SafetyPreflightError(f"invalid piezo range response: {exc}") from exc
    if not is_positive_finite(range_x) or not is_positive_finite(range_y):
        raise SafetyPreflightError("piezo X/Y ranges must be finite and > 0")
    x_limit = range_x / 2 - policy.piezo_safety_margin
    y_limit = range_y / 2 - policy.piezo_safety_margin
    if x_limit <= 0 or y_limit <= 0:
        raise SafetyPreflightError("piezo safety margin consumes the usable range")
    if any(abs(x) > x_limit or abs(y) > y_limit for x, y in desired.frame.corners()):
        raise SafetyPreflightError("rotated scan frame exceeds the usable piezo range")

    if _scan_status_value(client.send("Scan.StatusGet")) != STATUS_IDLE:
        raise SafetyPreflightError("a scan is already running")


def _validate_requested_safety(config: ScanConfig, policy: ScanSafetyPolicy) -> None:
    if config.pixels is not None and config.pixels > policy.max_pixels:
        raise SafetyPreflightError("requested pixels exceed the safety policy")
    if config.lines is not None and config.lines > policy.max_lines:
        raise SafetyPreflightError("requested lines exceed the safety policy")
    for value in (config.forward_line_time, config.backward_line_time):
        if value is not None and not policy.min_line_time <= value <= policy.max_line_time:
            raise SafetyPreflightError("requested line time is outside policy bounds")


def _validate_effective_safety(
    settings: ScanSettings, policy: ScanSafetyPolicy
) -> None:
    if not 2 <= settings.pixels <= policy.max_pixels:
        raise SafetyPreflightError("effective pixel count is outside policy bounds")
    if not 2 <= settings.lines <= policy.max_lines:
        raise SafetyPreflightError("effective line count is outside policy bounds")
    for value in (
        settings.speed.forward_time_per_line,
        settings.speed.backward_time_per_line,
    ):
        if not is_positive_finite(value) or not (
            policy.min_line_time <= value <= policy.max_line_time
        ):
            raise SafetyPreflightError("effective line time is outside policy bounds")
    for value in (
        settings.speed.forward_linear_speed,
        settings.speed.backward_linear_speed,
    ):
        if not is_positive_finite(value) or not (
            policy.min_linear_speed <= value <= policy.max_linear_speed
        ):
            raise SafetyPreflightError("effective linear speed is outside policy bounds")


def _validate_timeout_budget(config: ScanConfig, settings: ScanSettings) -> None:
    """Reject an explicit socket timeout before settings are written."""
    if config.acquisition_timeout is None:
        return
    estimate = estimate_scan_duration(settings)
    controller_timeout_ms = nanonis_timeout_ms(config, settings, estimate=estimate)
    resolve_acquisition_timeout(
        config,
        settings,
        controller_timeout_ms=controller_timeout_ms,
        estimate=estimate,
    )


def is_positive_finite(value: float) -> bool:
    return math.isfinite(value) and value > 0


def scan(
    nanonis: Any,
    *,
    safety_policy: ScanSafetyPolicy,
    nan_policy: NaNPolicy = NaNPolicy.WARN,
) -> ScanWorkflow:
    """Build a scan workflow from a NanonisInstrument or command client."""
    client = getattr(nanonis, "controller", nanonis)
    return ScanWorkflow(client, safety_policy=safety_policy, nan_policy=nan_policy)
