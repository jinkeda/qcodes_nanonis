import pytest

from nanonis.workflows.errors import StateRestorationError
from nanonis.workflows.models import (
    BiasRampPolicy,
    BiasRestoreMode,
    BiasSpectroscopySafetyPolicy,
    ZeroCrossingPolicy,
)
from nanonis.workflows.state import (
    RecoveryReport,
    RestorationTransaction,
    TipState,
    recover_bias_spectroscopy,
)

from .conftest import FakeController, RecoverableFakeController


def safety(mode=BiasRestoreMode.DIRECT):
    ramp = BiasRampPolicy(0.1, 0.0, ZeroCrossingPolicy.ALLOW)
    return BiasSpectroscopySafetyPolicy(
        max_abs_bias=10,
        max_abs_z_offset=1e-6,
        min_slew_rate=1e-6,
        max_slew_rate=100,
        bias_restore_mode=mode,
        bias_ramp=ramp if mode is BiasRestoreMode.STEPPED else None,
        allow_zero_crossing=True,
    )


class Participant:
    def __init__(self, events, name, failures=None):
        self.events = events
        self.name = name
        self.failures = failures or {}

    def restore(self, client):
        self.events.append(self.name)
        return self.failures


@pytest.mark.parametrize("raised", [None, RuntimeError("body"), KeyboardInterrupt()])
def test_restore_on_every_exit_and_reverse_order(raised):
    events = []
    client = FakeController()

    with pytest.raises(type(raised)) if raised is not None else _does_not_raise():
        with RestorationTransaction(client) as tx:
            tx.preserve("tip", Participant(events, "tip"))
            tx.preserve("settings", Participant(events, "settings"))
            if raised is not None:
                raise raised

    assert events == ["settings", "tip"]


def test_transaction_aggregates_both_scopes_and_carries_result():
    client = FakeController()
    result = object()
    with pytest.raises(StateRestorationError) as caught:
        with RestorationTransaction(client) as tx:
            tx.preserve(
                "tip", Participant([], "tip", {"bias": RuntimeError("bias")})
            )
            tx.preserve(
                "settings",
                Participant([], "settings", {"timing": RuntimeError("timing")}),
            )
            tx.attach_result(result)

    assert set(caught.value.failures) == {"tip.bias", "settings.timing"}
    assert caught.value.result is result


def test_tip_restore_order_and_best_effort():
    client = FakeController().script("Bias.Get", 0.4)
    client.fail("Bias.Set", RuntimeError("cannot set bias"))
    state = TipState(bias=0.1, current_setpoint=2e-10, feedback_enabled=True)

    failures = state.restore(client, safety())

    writes = [command for command, _, _ in client.sent]
    assert writes == [
        "ZCtrl.OnOffSet",
        "Bias.Get",
        "Bias.Set",
        "ZCtrl.SetpntSet",
        "ZCtrl.OnOffSet",
    ]
    assert set(failures) == {"bias"}


def test_stepped_restore_respects_maximum_step():
    client = FakeController().script("Bias.Get", 0.35)
    state = TipState(bias=0.0, current_setpoint=1.0, feedback_enabled=False)

    assert state.restore(client, safety(BiasRestoreMode.STEPPED)) == {}

    steps = [args[0] for cmd, args, _ in client.sent if cmd == "Bias.Set"]
    assert len(steps) == 4
    assert steps[-1] == pytest.approx(0.0)
    assert all(abs(b - a) <= 0.1 for a, b in zip([0.35] + steps, steps))


def test_recover_returns_early_when_already_stopped():
    client = RecoverableFakeController().script("BiasSpectr.StatusGet", 0)

    report = recover_bias_spectroscopy(client, timeout=1)

    assert report.restoration_allowed
    assert [entry[0] for entry in client.sent] == ["BiasSpectr.StatusGet"]


def test_recover_stop_and_wait_before_restoration():
    client = RecoverableFakeController().script("BiasSpectr.StatusGet", 1, 1, 0)

    report = recover_bias_spectroscopy(client, timeout=1, poll_interval=0.001)

    assert report.restoration_allowed
    assert [entry[0] for entry in client.sent] == [
        "BiasSpectr.StatusGet",
        "BiasSpectr.Stop",
        "BiasSpectr.StatusGet",
        "BiasSpectr.StatusGet",
    ]


def test_failed_reconnect_gates_all_restoration_writes():
    client = RecoverableFakeController()
    client.reconnect_error = RuntimeError("offline")
    report = recover_bias_spectroscopy(client, timeout=1)
    events = []

    with pytest.raises(StateRestorationError) as caught:
        with RestorationTransaction(client) as tx:
            tx.preserve("tip", Participant(events, "tip"))
            tx.record_recovery(report, origin=RuntimeError("timeout"))
            raise RuntimeError("timeout")

    assert events == []
    assert isinstance(caught.value.recovery_error, RuntimeError)


def test_second_interrupt_marks_stop_unknown_and_carries_both_interrupts():
    client = RecoverableFakeController().script("BiasSpectr.StatusGet", 1)
    second = KeyboardInterrupt("second")
    client.fail("BiasSpectr.Stop", second)
    first = KeyboardInterrupt("first")
    report = recover_bias_spectroscopy(client, timeout=1)

    assert report.spectroscopy_stopped is None
    assert report.errors == (second,)
    with pytest.raises(StateRestorationError) as caught:
        with RestorationTransaction(client) as tx:
            tx.record_recovery(report, origin=first)
            raise first
    assert caught.value.original_error is first
    assert caught.value.recovery_error is second


def test_restoration_allowed_requires_both_conditions():
    assert RecoveryReport(True, True).restoration_allowed
    assert not RecoveryReport(False, True).restoration_allowed
    assert not RecoveryReport(True, False).restoration_allowed
    assert not RecoveryReport(True, None).restoration_allowed


class _does_not_raise:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False
