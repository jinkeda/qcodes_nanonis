"""Recovery-gated, reverse-order state restoration."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping

from nanonis.protocol import TransportState

from .errors import RecoveryError, StateRestorationError, WorkflowError
from .models import (
    BiasRestoreMode,
    TipRestorePolicy,
    ZeroCrossingPolicy,
)
from .protocols import CommandClient, RecoverableCommandClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecoveryReport:
    transport_ready: bool
    module_stopped: bool | None
    errors: tuple[BaseException, ...] = ()

    @property
    def spectroscopy_stopped(self) -> bool | None:
        """Compatibility alias retained for the spectroscopy vertical."""
        return self.module_stopped

    @property
    def restoration_allowed(self) -> bool:
        return self.transport_ready and self.module_stopped is True


StopOperation = Callable[[CommandClient], None]
StoppedPredicate = Callable[[CommandClient], bool]


def recover_module(
    client: RecoverableCommandClient,
    *,
    stop: StopOperation,
    status_stopped: StoppedPredicate,
    timeout: float,
    poll_interval: float = 0.1,
) -> RecoveryReport:
    """Reconnect, stop an arbitrary module, and confirm that writes are safe."""
    errors: list[BaseException] = []
    try:
        client.reconnect()
    except BaseException as exc:
        return RecoveryReport(False, None, (exc,))

    try:
        if status_stopped(client):
            return RecoveryReport(_transport_ready(client), True)
        stop(client)
        deadline = time.monotonic() + timeout
        while True:
            if status_stopped(client):
                return RecoveryReport(_transport_ready(client), True, tuple(errors))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return RecoveryReport(_transport_ready(client), False, tuple(errors))
            time.sleep(min(poll_interval, remaining))
    except BaseException as exc:
        errors.append(exc)
        return RecoveryReport(_transport_ready(client), None, tuple(errors))


def recover_bias_spectroscopy(
    client: RecoverableCommandClient,
    *,
    timeout: float,
    poll_interval: float = 0.1,
) -> RecoveryReport:
    """Compatibility wrapper around :func:`recover_module`."""
    return recover_module(
        client,
        stop=lambda value: value.send("BiasSpectr.Stop"),
        status_stopped=_status_is_stopped,
        timeout=timeout,
        poll_interval=poll_interval,
    )


def _status_is_stopped(client: CommandClient) -> bool:
    value = client.send("BiasSpectr.StatusGet")
    if isinstance(value, Mapping):
        value = value["status"]
    return int(value) == 0


def _transport_ready(client: Any) -> bool:
    state = getattr(client, "transport_state", None)
    if state is not None:
        return state is TransportState.READY or state == TransportState.READY
    return bool(getattr(client, "is_connected", True))


@dataclass(frozen=True)
class TipState:
    bias: float
    current_setpoint: float
    feedback_enabled: bool

    @classmethod
    def snapshot(cls, client: CommandClient) -> "TipState":
        return cls(
            bias=float(client.send("Bias.Get")),
            current_setpoint=float(client.send("ZCtrl.SetpntGet")),
            feedback_enabled=bool(client.send("ZCtrl.OnOffGet")),
        )

    def restore(
        self,
        client: CommandClient,
        safety_policy: TipRestorePolicy,
    ) -> dict[str, BaseException]:
        failures: dict[str, BaseException] = {}
        feedback_safe = True
        if safety_policy.feedback_off_during_restore:
            try:
                logger.info("Disabling Z feedback before bias restoration")
                client.send("ZCtrl.OnOffSet", 0)
            except BaseException as exc:
                failures["feedback_disable"] = exc
                feedback_safe = False

        if feedback_safe:
            try:
                self._restore_bias(client, safety_policy)
            except BaseException as exc:
                failures["bias"] = exc
        else:
            failures["bias"] = WorkflowError(
                "bias restoration skipped because feedback could not be disabled"
            )

        try:
            logger.info("Restoring Z-controller current setpoint to %g", self.current_setpoint)
            client.send("ZCtrl.SetpntSet", self.current_setpoint)
        except BaseException as exc:
            failures["setpoint"] = exc

        try:
            logger.info("Restoring Z feedback state to %s", self.feedback_enabled)
            client.send("ZCtrl.OnOffSet", 1 if self.feedback_enabled else 0)
        except BaseException as exc:
            failures["feedback"] = exc
        return failures

    def _restore_bias(
        self,
        client: CommandClient,
        safety_policy: TipRestorePolicy,
    ) -> None:
        current = float(client.send("Bias.Get"))
        crossing = current * self.bias < 0
        ramp_allows = (
            safety_policy.bias_ramp is None
            or safety_policy.bias_ramp.zero_crossing_policy is ZeroCrossingPolicy.ALLOW
        )
        if crossing and not (safety_policy.allow_zero_crossing and ramp_allows):
            raise WorkflowError(
                f"bias restoration from {current:g} V to {self.bias:g} V crosses zero"
            )

        mode = safety_policy.bias_restore_mode
        if mode is BiasRestoreMode.DIRECT:
            logger.info("Restoring bias directly to %g V", self.bias)
            client.send("Bias.Set", self.bias)
            return
        if mode is BiasRestoreMode.EXTERNAL:
            callback = safety_policy.external_bias_restorer
            if callback is None:
                raise WorkflowError("external bias restorer is not configured")
            logger.info("Restoring bias through external policy to %g V", self.bias)
            callback(client, self.bias)
            return

        ramp = safety_policy.bias_ramp
        if ramp is None:
            raise WorkflowError("stepped bias ramp is not configured")
        steps = max(1, math.ceil(abs(self.bias - current) / ramp.max_step))
        for index in range(1, steps + 1):
            value = current + (self.bias - current) * index / steps
            logger.info("Restoring bias step %d/%d to %g V", index, steps, value)
            client.send("Bias.Set", value)
            if ramp.dwell_time and index < steps:
                time.sleep(ramp.dwell_time)


Restorer = Callable[[Any], Mapping[str, BaseException] | None]


class RestorationTransaction:
    """Coordinate all state participants and aggregate every cleanup failure."""

    def __init__(self, client: CommandClient) -> None:
        self._client = client
        self._participants: list[tuple[str, Any, Restorer, bool]] = []
        self._recovery_report: RecoveryReport | None = None
        self._recovery_origin: BaseException | None = None
        self._result: Any = None

    def __enter__(self) -> "RestorationTransaction":
        return self

    def preserve(
        self,
        name: str,
        state: Any,
        *,
        restorer: Restorer | None = None,
        enabled: bool = True,
    ) -> Any:
        if any(existing == name for existing, *_ in self._participants):
            raise ValueError(f"participant {name!r} is already registered")
        selected = restorer or (lambda value: value.restore(self._client))
        self._participants.append((name, state, selected, enabled))
        return state

    def attach_result(self, result: Any) -> None:
        self._result = result

    def record_recovery(
        self, report: RecoveryReport, *, origin: BaseException | None = None
    ) -> None:
        self._recovery_report = report
        self._recovery_origin = origin

    def __exit__(self, exc_type, exc, traceback) -> Literal[False]:
        original = exc
        report = self._recovery_report
        if report is None and getattr(
            self._client, "transport_state", TransportState.READY
        ) is TransportState.DESYNCHRONIZED:
            report = RecoveryReport(False, None)

        if report is not None and not report.restoration_allowed:
            recovery_error = _recovery_error(report)
            error = StateRestorationError(
                original_error=original,
                recovery_error=recovery_error,
                failures={},
                result=self._result,
            )
            if original is not None:
                raise error from original
            raise error

        failures: dict[str, BaseException] = {}
        for name, state, restorer, enabled in reversed(self._participants):
            if not enabled:
                continue
            logger.info("Restoring workflow participant %s", name)
            try:
                participant_failures = restorer(state) or {}
                for field, failure in participant_failures.items():
                    failures[f"{name}.{field}"] = failure
            except BaseException as failure:
                failures[name] = failure

        if failures:
            error = StateRestorationError(
                original_error=original,
                failures=failures,
                result=self._result,
            )
            if original is not None:
                raise error from original
            raise error
        return False


def _recovery_error(report: RecoveryReport) -> BaseException:
    if len(report.errors) == 1:
        return report.errors[0]
    reason = (
        "transport did not recover"
        if not report.transport_ready
        else "module stop was not confirmed"
    )
    return RecoveryError(reason, report.errors)
