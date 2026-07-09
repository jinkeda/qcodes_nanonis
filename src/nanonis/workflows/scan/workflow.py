"""Transactional, one-frame Nanonis scan workflow."""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

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
from .models import ScanConfig, ScanRegion, ScanSafetyPolicy, ScanSettings
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

# Scan.WaitEndOfLine "Type of movement" value for the forward/trace pass.
# Characterized on a real controller (examples/verify_waitendofline.py): the tip
# emits one WaitEndOfLine return per movement -- roughly two per image row
# (trace then retrace) -- plus a short, variable-length startup transient. A new
# image row begins at each trace return whose line number is >= 1, which is how
# run_partial counts rows independently of the transient.
TRACE_MOVEMENT = 0
# Safety bound on returns per requested row: ~2 movements/row plus startup slack,
# so the per-line loop cannot spin forever if a controller's movement encoding
# differs from the characterized convention.
RETURNS_PER_ROW_BUDGET = 2
PARTIAL_STARTUP_RETURN_BUDGET = 6

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
        region: ScanRegion | None = None,
        *,
        unsafe_skip_preflight: bool = False,
    ) -> ScanResult:
        if not isinstance(config, ScanConfig):
            raise TypeError("config must be ScanConfig")
        if region is not None and not isinstance(region, ScanRegion):
            raise TypeError("region must be ScanRegion or None")
        _validate_requested_safety(config, self._safety)
        if config.restore_tip_state and self._safety.tip is None:
            raise SafetyPreflightError(
                "restore_tip_state requires ScanSafetyPolicy.tip"
            )
        if not unsafe_skip_preflight:
            preflight_scan(self._client, config, self._safety, region)

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
            desired = original.patch(config, region)
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
                    requested_region=region,
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

    def run_partial(
        self,
        config: ScanConfig,
        region: ScanRegion | None = None,
        *,
        max_lines: int,
        on_line: Callable[[int, int, int], bool | None] | None = None,
        unsafe_skip_preflight: bool = False,
    ) -> ScanResult:
        """Scan at most ``max_lines`` image rows of the frame, then stop early.

        Unlike :meth:`run`, this drives the raster line by line with
        ``Scan.WaitEndOfLine`` and issues ``Scan.Action(Stop)`` once
        ``max_lines`` image rows have been acquired (or sooner, if ``on_line``
        vetoes). The returned :class:`ScanResult` is the partially filled
        frame buffer; rows that were never scanned come back as NaN and are
        handled by the configured :class:`NaNPolicy` (use ``WARN``/``ALLOW``,
        not ``RAISE``). Partial scans are not auto-saved, so
        ``result.saved_path`` is empty.

        ``max_lines`` counts **image rows**, not raw ``WaitEndOfLine`` returns.
        On a characterized controller the tip emits ~2 returns per row
        (trace + retrace) plus a short startup transient; a row is counted at
        each trace return (``movement == TRACE_MOVEMENT`` with line number
        >= 1). See ``examples/verify_waitendofline.py``.

        ``on_line`` receives ``(line_number, movement, pass_number)`` straight
        from the controller after **every** ``WaitEndOfLine`` return (i.e. once
        per movement, not once per row); returning ``False`` stops the scan
        immediately.

        ``config.acquisition_timeout`` governs the whole-frame
        ``WaitEndOfScan`` and is ignored here; a per-line socket timeout is
        derived from the effective line timing instead.
        """
        if not isinstance(config, ScanConfig):
            raise TypeError("config must be ScanConfig")
        if region is not None and not isinstance(region, ScanRegion):
            raise TypeError("region must be ScanRegion or None")
        if not isinstance(max_lines, int) or isinstance(max_lines, bool) or max_lines < 1:
            raise ValueError("max_lines must be a positive integer")
        _validate_requested_safety(config, self._safety)
        if config.restore_tip_state and self._safety.tip is None:
            raise SafetyPreflightError(
                "restore_tip_state requires ScanSafetyPolicy.tip"
            )
        if not unsafe_skip_preflight:
            preflight_scan(self._client, config, self._safety, region)

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
            desired = original.patch(config, region)
            _validate_effective_safety(desired, self._safety)
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

            target_rows = min(max_lines, effective.lines)
            line_timeout_ms = nanonis_line_timeout_ms(effective)
            line_socket_timeout = line_timeout_ms / 1000 * 1.5 + 5.0
            estimate = _partial_scan_estimate(effective, target_rows)
            # Bound total returns so the loop cannot spin forever if the
            # controller's movement encoding differs from TRACE_MOVEMENT.
            max_returns = (
                target_rows * RETURNS_PER_ROW_BUDGET + PARTIAL_STARTUP_RETURN_BUDGET
            )
            started_at = datetime.now(timezone.utc)
            started_monotonic = time.monotonic()
            start_attempted = False
            completed = False
            rows_done = 0
            try:
                start_attempted = True
                self._client.send(
                    "Scan.Action",
                    ACTION_START,
                    DIRECTION_UP if config.direction == "up" else DIRECTION_DOWN,
                )
                for _ in range(max_returns):
                    wait = self._client.send(
                        "Scan.WaitEndOfLine",
                        line_timeout_ms,
                        timeout=line_socket_timeout,
                    )
                    if not isinstance(wait, Mapping):
                        raise ScanResponseError(
                            "Scan.WaitEndOfLine must return a mapping"
                        )
                    try:
                        timeout_status = int(wait["timeout_status"])
                    except (KeyError, TypeError, ValueError) as exc:
                        raise ScanResponseError(
                            f"invalid Scan.WaitEndOfLine timeout status: {exc}"
                        ) from exc
                    if timeout_status == WAIT_TIMED_OUT:
                        raise ScanTimeoutError(
                            f"scan line exceeded Nanonis timeout {line_timeout_ms} ms"
                        )
                    if timeout_status != WAIT_COMPLETED:
                        raise ScanResponseError(
                            f"unknown WaitEndOfLine timeout status {timeout_status}"
                        )
                    try:
                        line_number = int(wait["line_number"])
                        movement = int(wait["type_of_movement"])
                        pass_number = int(wait["pass_number"])
                    except (KeyError, TypeError, ValueError) as exc:
                        raise ScanResponseError(
                            f"invalid Scan.WaitEndOfLine line metadata: {exc}"
                        ) from exc
                    if on_line is not None and (
                        on_line(line_number, movement, pass_number) is False
                    ):
                        break
                    # A new image row starts at each trace return; the startup
                    # transient (line_number < 1, or non-trace movements) does
                    # not advance the row count.
                    if movement == TRACE_MOVEMENT and line_number >= 1:
                        rows_done += 1
                        if rows_done >= target_rows:
                            break
                    # The frame can finish on its own (e.g. max_lines >= frame
                    # lines, or an external stop); avoid waiting for a line that
                    # will never arrive.
                    if _scan_status_value(
                        self._client.send("Scan.StatusGet")
                    ) == STATUS_IDLE:
                        break
                else:
                    logger.warning(
                        "Scan.WaitEndOfLine returned %d times but only %d of %d "
                        "rows were counted; the controller movement encoding may "
                        "differ from the characterized trace convention",
                        max_returns,
                        rows_done,
                        target_rows,
                    )
                # Abandon any remaining lines; a no-op if already idle.
                self._client.send("Scan.Action", ACTION_STOP, 0)
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
                    saved_path="",
                    config=config,
                    effective=effective,
                    requested_region=region,
                    acquisition_started_at=started_at,
                    acquisition_finished_at=finished_at,
                    acquisition_duration=finished_monotonic - started_monotonic,
                    estimated_acquisition_duration=estimate,
                    acquisition_timeout_used=line_socket_timeout,
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


def _partial_scan_estimate(settings: ScanSettings, lines: int) -> float:
    """Estimate the duration of a partial raster of ``lines`` lines."""
    forward = settings.speed.forward_time_per_line
    backward = settings.speed.backward_time_per_line
    if any(not math.isfinite(value) or value <= 0 for value in (forward, backward)):
        logger.warning(
            "Using a 60 s fallback partial-scan estimate because line timing is incomplete"
        )
        return 60.0
    return max(0.0, lines * (forward + backward) + POSITIONING_MARGIN_SECONDS)


def nanonis_line_timeout_ms(effective: ScanSettings) -> int:
    """Controller-side timeout for a single ``Scan.WaitEndOfLine`` call."""
    forward = effective.speed.forward_time_per_line
    backward = effective.speed.backward_time_per_line
    if any(not math.isfinite(value) or value <= 0 for value in (forward, backward)):
        logger.warning(
            "Using a 60 s fallback line timeout because line timing is incomplete"
        )
        per_line = 60.0
    else:
        per_line = forward + backward
    return min(
        MAX_NANONIS_TIMEOUT_MS,
        max(1, math.ceil(per_line * 1000 + NANONIS_TIMEOUT_MARGIN_MS)),
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
    region: ScanRegion | None = None,
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
    desired = current.patch(config, region)
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
