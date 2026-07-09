from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

import numpy as np
import pytest
import nanonis.workflows.datalog.workflow as datalog_workflow_module

from nanonis.protocol import NanonisCommandError, NanonisTimeoutError
from nanonis.types import NaNPolicy
from nanonis.workflows import (
    CancelToken,
    NonFiniteTimeTraceDataError,
    TimeTraceConfig,
    TimeTraceResponseError,
    TimeTraceResult,
    TimeTraceWorkflow,
    SampleEvent,
)

from ..conftest import FakeController


def version(value: str = "5.0") -> dict[str, object]:
    return {
        "product_line": "SPM",
        "version": value,
        "host_app_release": 1,
        "rt_engine_release": 1,
    }


def vals(*values: float, declared: object | None = None) -> dict[str, object]:
    return {
        "signals_values_size": len(values) if declared is None else declared,
        "signals_values": list(values),
    }


def names(*values: str, declared: object | None = None) -> dict[str, object]:
    return {
        "signals_names_number": len(values) if declared is None else declared,
        "signals_names": list(values),
    }


def scripted_client(sample_count: int, *rows: tuple[float, ...]) -> FakeController:
    client = FakeController().script("Util.VersionGet", version())
    if not rows:
        rows = tuple((float(k),) for k in range(sample_count))
    client.script("Signals.ValsGet", *(vals(*row) for row in rows))
    return client


def test_happy_path_is_read_only_and_immutable() -> None:
    client = scripted_client(2, (1.0, 2.0), (3.0, 4.0))
    config = TimeTraceConfig(
        (2, 4), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
    )
    result = TimeTraceWorkflow(client).run(config)
    assert result.values.shape == (2, 2)
    np.testing.assert_allclose(result.values, [[1, 3], [2, 4]])
    assert np.all(np.diff(result.elapsed_s) > 0)
    assert not result.values.flags.writeable
    assert result.nanonis_version == "5.0"
    assert result.to_metadata()["config"] == {
        "signal_indexes": [2, 4],
        "duration_s": 0.04,
        "sample_interval_s": 0.04,
        "wait_for_newest_data": True,
        "resolve_names": False,
    }
    assert "nanonis_version" not in result.to_metadata()
    assert result.to_metadata()["controller"] == {"nanonis_version": "5.0"}
    assert [call[0] for call in client.sent] == [
        "Util.VersionGet",
        "Signals.ValsGet",
        "Signals.ValsGet",
    ]
    assert client.sent[1][1] == (2, (2, 4), 1)
    assert all(".Set" not in command for command, _, _ in client.sent)


@pytest.mark.parametrize(
    "response",
    [
        None,
        {"signals_values_size": 1},
        {"signals_values": [1.0]},
        vals(1.0, declared="1"),
        vals(1.0, declared=2),
        vals(),
        vals(1.0, 2.0),
        {"signals_values_size": 1, "signals_values": [[1.0]]},
    ],
)
def test_malformed_values_response_raises(response: object) -> None:
    client = FakeController().script("Util.VersionGet", version())
    client.script("Signals.ValsGet", response)
    config = TimeTraceConfig(
        (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
    )
    with pytest.raises(TimeTraceResponseError):
        TimeTraceWorkflow(client).run(config)


@pytest.mark.parametrize(
    "response",
    [
        names("I", declared=2),
        names("I"),
        {"signals_names": ["I"]},
        {"signals_names_number": 1},
        {"signals_names_number": "1", "signals_names": ["I"]},
    ],
)
def test_malformed_names_response_raises(response: object) -> None:
    client = FakeController().script("Util.VersionGet", version())
    client.script("Signals.NamesGet", response)
    config = TimeTraceConfig((1,), duration_s=0.04, sample_interval_s=0.04)
    with pytest.raises(TimeTraceResponseError):
        TimeTraceWorkflow(client).run(config)


def test_name_resolution_and_accessors() -> None:
    client = scripted_client(2, (1.0, 2.0), (3.0, 4.0))
    client.script("Signals.NamesGet", names("Z", "I", "Z"))
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig((0, 2), duration_s=0.04, sample_interval_s=0.04)
    )
    np.testing.assert_allclose(result.signal_by_index(0), [1.0, 3.0])
    with pytest.raises(KeyError):
        result.signal_by_index(1)
    with pytest.raises(ValueError, match="indexes.*signal_by_index"):
        result.signal_by_name("Z")
    with pytest.raises(ValueError, match="not recorded"):
        result.signal_by_name("I")


def test_unresolved_names_accessor_raises() -> None:
    client = scripted_client(2)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        )
    )
    with pytest.raises(ValueError, match="not resolved"):
        result.signal_by_name("Z")


def test_cancel_returns_partial_result() -> None:
    token = CancelToken()
    client = FakeController().script("Util.VersionGet", version())

    def cancel_after_first(command, args, timeout):
        token.cancel()
        return vals(1.0)

    client.script("Signals.ValsGet", cancel_after_first)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.4, sample_interval_s=0.04, resolve_names=False
        ),
        cancel=token,
    )
    assert result.cancelled
    assert result.n_samples == 1


def test_cancel_while_late_is_observed() -> None:
    token = CancelToken()
    client = FakeController().script("Util.VersionGet", version())

    def slow_first(command, args, timeout):
        threading.Timer(0.01, token.cancel).start()
        time.sleep(0.08)
        return vals(1.0)

    client.script("Signals.ValsGet", slow_first)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.16, sample_interval_s=0.04, resolve_names=False
        ),
        cancel=token,
    )
    assert result.cancelled
    assert result.n_samples == 1


def test_timeout_propagates_without_partial_result() -> None:
    error = NanonisTimeoutError("timeout")
    calls = 0

    def response(command, args, timeout):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise error
        return vals(float(calls))

    client = (
        FakeController()
        .script("Util.VersionGet", version())
        .script("Signals.ValsGet", response, response, response)
    )
    with pytest.raises(NanonisTimeoutError):
        TimeTraceWorkflow(client).run(
            TimeTraceConfig(
                (0,), duration_s=0.08, sample_interval_s=0.04, resolve_names=False
            )
        )


@pytest.mark.parametrize(
    ("duration", "interval", "expected"),
    [(1.0, 1.0, 2), (0.3, 0.1, 4), (0.35, 0.1, 4), (60.0, 0.1, 601)],
)
def test_float_safe_sample_count(
    duration: float, interval: float, expected: int
) -> None:
    assert TimeTraceConfig((0,), duration, interval).n_samples == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"signal_indexes": ()},
        {"signal_indexes": (0, 0)},
        {"signal_indexes": (-1,)},
        {"signal_indexes": (128,)},
        {"duration_s": 0.0},
        {"duration_s": float("nan")},
        {"sample_interval_s": 0.0},
        {"sample_interval_s": 2.0},
    ],
)
def test_config_validation(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "signal_indexes": (0,),
        "duration_s": 1.0,
        "sample_interval_s": 1.0,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        TimeTraceConfig(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("policy", [NaNPolicy.ALLOW, NaNPolicy.WARN])
def test_non_finite_allow_and_warn(policy: NaNPolicy, caplog) -> None:
    client = scripted_client(2, (float("nan"),), (float("inf"),))
    with caplog.at_level(logging.WARNING):
        result = TimeTraceWorkflow(client, nan_policy=policy).run(
            TimeTraceConfig(
                (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
            )
        )
    assert result.n_samples == 2
    assert ("Time-trace data contains" in caplog.text) is (policy is NaNPolicy.WARN)


def test_non_finite_raise_retains_result_without_complete_progress() -> None:
    client = scripted_client(2, (float("nan"),), (1.0,))
    messages: list[str] = []
    with pytest.raises(NonFiniteTimeTraceDataError) as caught:
        TimeTraceWorkflow(client, nan_policy=NaNPolicy.RAISE).run(
            TimeTraceConfig(
                (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
            ),
            on_progress=lambda event: messages.append(event.message),
        )
    assert caught.value.result.n_samples == 2
    assert caught.value.diagnostics.affected_signal_indexes == (0,)
    assert "complete" not in messages


class FakeClock:
    def __init__(self, *, sleep_overshoot: float = 0.0) -> None:
        self.now = 100.0
        self.sleep_overshoot = sleep_overshoot

    def monotonic(self) -> float:
        return self.now

    def sleep(self, timeout: float) -> None:
        self.now += timeout + self.sleep_overshoot

    def advance(self, duration: float) -> None:
        self.now += duration


def test_sub_tolerance_sleep_jitter_preserves_nominal_grid(monkeypatch) -> None:
    clock = FakeClock(sleep_overshoot=0.01)
    monkeypatch.setattr(datalog_workflow_module.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(datalog_workflow_module.time, "sleep", clock.sleep)
    client = scripted_client(10)

    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.36, sample_interval_s=0.04, resolve_names=False
        )
    )

    assert result.late_sample_count == 0
    # Each wakeup is 10 ms late, but the lateness does not accumulate. An
    # unconditional acquisition_started + interval rebase would end at 0.45 s.
    assert result.elapsed_s[-1] == pytest.approx(0.37)


def test_cancel_wait_overshoot_is_counted_as_late(monkeypatch) -> None:
    clock = FakeClock()
    monkeypatch.setattr(datalog_workflow_module.time, "monotonic", clock.monotonic)

    class OversleepToken:
        cancelled = False

        def wait(self, timeout: float) -> bool:
            clock.advance(timeout + 0.03)
            return False

    client = scripted_client(2)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        ),
        cancel=OversleepToken(),  # type: ignore[arg-type]
    )

    assert result.late_sample_count == 1
    assert result.elapsed_s[-1] == pytest.approx(0.07)


def test_first_sample_never_counts_late_but_stall_rebases() -> None:
    starts: list[float] = []
    client = FakeController().script("Util.VersionGet", version())

    def row(command, args, timeout):
        starts.append(time.monotonic())
        if len(starts) == 2:
            time.sleep(0.08)
        return vals(float(len(starts)))

    client.script("Signals.ValsGet", row, row, row, row)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.12, sample_interval_s=0.04, resolve_names=False
        )
    )
    assert result.late_sample_count == 1
    assert starts[3] - starts[2] >= 0.03


def test_version_command_error_is_allowed_but_timeout_propagates() -> None:
    client = FakeController().fail(
        "Util.VersionGet", NanonisCommandError("Util.VersionGet", "unsupported")
    )
    client.script("Signals.ValsGet", vals(1.0), vals(2.0))
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
        )
    )
    assert result.nanonis_version is None

    timed_out = FakeController().fail("Util.VersionGet", NanonisTimeoutError("timeout"))
    with pytest.raises(NanonisTimeoutError):
        TimeTraceWorkflow(timed_out).run(
            TimeTraceConfig(
                (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
            )
        )
    assert [command for command, _, _ in timed_out.sent] == ["Util.VersionGet"]


def test_result_metadata_and_validation() -> None:
    now = datetime.now(timezone.utc)
    result = TimeTraceResult(
        signal_indexes=(0,),
        signal_names=("I",),
        elapsed_s=np.array([0.01, 0.02]),
        values=np.array([[1.0, 2.0]]),
        requested_interval_s=0.01,
        started_at=now,
        finished_at=now,
        late_sample_count=0,
        cancelled=False,
        nanonis_version="5.0",
    )
    metadata = result.to_metadata()
    assert metadata["n_samples"] == 2
    assert metadata["software"]
    with pytest.raises(ValueError, match="strictly increasing"):
        TimeTraceResult(
            signal_indexes=(0,),
            signal_names=(),
            elapsed_s=np.array([0.01, 0.01]),
            values=np.array([[1.0, 2.0]]),
            requested_interval_s=0.01,
            started_at=now,
            finished_at=now,
            late_sample_count=0,
            cancelled=False,
            nanonis_version=None,
        )


def test_sample_events_match_stored_result() -> None:
    events: list[SampleEvent] = []
    result = TimeTraceWorkflow(
        scripted_client(3, (1.0, 2.0), (3.0, 4.0), (5.0, 6.0))
    ).run(
        TimeTraceConfig(
            (0, 1), duration_s=0.08, sample_interval_s=0.04,
            resolve_names=False,
        ),
        on_sample=events.append,
    )

    assert [event.sample_index for event in events] == [0, 1, 2]
    assert all(event.workflow == "datalog.time_trace" for event in events)
    assert all(isinstance(event.values, tuple) for event in events)
    np.testing.assert_array_equal(
        [event.elapsed_s for event in events], result.elapsed_s
    )
    np.testing.assert_array_equal(
        np.asarray([event.values for event in events]).T, result.values
    )


def test_sample_callback_fails_once_and_logs_summary(caplog) -> None:
    calls: list[int] = []

    def callback(event: SampleEvent) -> None:
        calls.append(event.sample_index)
        if event.sample_index == 2:
            raise RuntimeError("display failed")

    with caplog.at_level(logging.WARNING):
        result = TimeTraceWorkflow(scripted_client(5)).run(
            TimeTraceConfig(
                (0,), duration_s=0.16, sample_interval_s=0.04,
                resolve_names=False,
            ),
            on_sample=callback,
        )

    assert result.n_samples == 5
    assert calls == [0, 1, 2]
    assert caplog.text.count("sample callback failed") == 1
    assert caplog.text.count("stopped at sample 2") == 1


def test_sample_callback_failure_summary_survives_transport_error(caplog) -> None:
    calls = 0

    def response(command, args, timeout):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise NanonisTimeoutError("later timeout")
        return vals(float(calls))

    client = FakeController().script("Util.VersionGet", version())
    client.script("Signals.ValsGet", *(response for _ in range(5)))

    def callback(event: SampleEvent) -> None:
        if event.sample_index == 2:
            raise RuntimeError("display failed")

    with caplog.at_level(logging.WARNING), pytest.raises(NanonisTimeoutError):
        TimeTraceWorkflow(client).run(
            TimeTraceConfig(
                (0,), duration_s=0.16, sample_interval_s=0.04,
                resolve_names=False,
            ),
            on_sample=callback,
        )
    assert "stopped at sample 2" in caplog.text


def test_slow_sample_callback_affects_next_deadline_only(monkeypatch) -> None:
    clock = FakeClock()
    monkeypatch.setattr(datalog_workflow_module.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(datalog_workflow_module.time, "sleep", clock.sleep)
    config = TimeTraceConfig(
        (0,), duration_s=0.08, sample_interval_s=0.04, resolve_names=False
    )

    slow_first = TimeTraceWorkflow(scripted_client(3)).run(
        config,
        on_sample=lambda event: clock.advance(0.07)
        if event.sample_index == 0
        else None,
    )
    assert slow_first.late_sample_count == 1

    clock.now = 100.0
    slow_final = TimeTraceWorkflow(scripted_client(3)).run(
        config,
        on_sample=lambda event: clock.advance(0.07)
        if event.sample_index == 2
        else None,
    )
    assert slow_final.late_sample_count == 0


def test_cancelled_trace_emits_exactly_its_stored_samples() -> None:
    token = CancelToken()
    events: list[SampleEvent] = []
    client = FakeController().script("Util.VersionGet", version())

    def first(command, args, timeout):
        token.cancel()
        return vals(1.0)

    client.script("Signals.ValsGet", first)
    result = TimeTraceWorkflow(client).run(
        TimeTraceConfig(
            (0,), duration_s=0.4, sample_interval_s=0.04, resolve_names=False
        ),
        cancel=token,
        on_sample=events.append,
    )
    assert len(events) == result.n_samples == 1


def test_none_sample_callback_allocates_no_events(monkeypatch) -> None:
    baseline_client = scripted_client(2)
    config = TimeTraceConfig(
        (0,), duration_s=0.04, sample_interval_s=0.04, resolve_names=False
    )
    baseline = TimeTraceWorkflow(baseline_client).run(config)

    def forbidden_event(*args, **kwargs):
        raise AssertionError("SampleEvent must not be constructed")

    monkeypatch.setattr(datalog_workflow_module, "SampleEvent", forbidden_event)
    explicit_client = scripted_client(2)
    explicit = TimeTraceWorkflow(explicit_client).run(config, on_sample=None)
    assert explicit_client.sent == baseline_client.sent
    np.testing.assert_array_equal(explicit.values, baseline.values)
