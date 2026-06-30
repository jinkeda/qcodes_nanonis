from dataclasses import replace

import numpy as np
import pytest

from nanonis.protocol import NanonisTimeoutError
from nanonis.workflows import (
    BiasRestoreMode,
    BiasSpectroscopyConfig,
    BiasSpectroscopySafetyPolicy,
    BiasSpectroscopyWorkflow,
    SafetyPreflightError,
    StateRestorationError,
    estimate_acquisition_duration,
    parse_bias_range,
    preflight_bias_spectroscopy,
)

from .conftest import RecoverableFakeController


def safety():
    return BiasSpectroscopySafetyPolicy(
        max_abs_bias=2,
        max_abs_z_offset=1e-7,
        min_slew_rate=0.01,
        max_slew_rate=10,
        bias_restore_mode=BiasRestoreMode.DIRECT,
        bias_ramp=None,
        allow_zero_crossing=True,
    )


def config(**changes):
    value = BiasSpectroscopyConfig(-1, 1, 3, (0, 1), restore_tip_state=True)
    return replace(value, **changes)


def chs(indexes=(0, 1)):
    return {"channel_indexes": indexes}


def props(*, points=4, sweeps=2, backward=0, save_all=1):
    return {
        "save_all": save_all,
        "num_sweeps": sweeps,
        "backward_sweep": backward,
        "num_points": points,
        "parameters": ["Start"],
        "fixed_parameters": ["Z"],
        "autosave": 1,
        "show_save_dialog": 0,
    }


def timing(*, z=2e-9, slew=2.0, integration=0.02, settling=0.01):
    return {
        "z_averaging_time_s": 0.1,
        "z_offset_m": z,
        "initial_settling_time_s": 0.2,
        "maximum_slew_rate_v_s": slew,
        "settling_time_s": settling,
        "integration_time": integration,
        "end_settling_time_s": 0.1,
        "z_control_time_s": 0.1,
    }


def advanced():
    return {
        "reset_bias": 0,
        "z_controller_hold": 1,
        "record_final_z": 0,
        "lockin_run": 0,
    }


def limits(start=-0.5, stop=0.5):
    return {"start_value_v": start, "end_value_v": stop}


def start_response():
    return {
        "channels_names": ["Current (A)", "Bias (V)"],
        "num_channels": 2,
        "data_rows": 2,
        "data_columns": 3,
        "data": np.arange(6).reshape(2, 3),
        "num_parameters": 2,
        "parameters": [0.0, -1.0],
    }


def scripted_controller(*, start=None):
    client = RecoverableFakeController()
    client.script("Bias.RangeGet", {"bias_ranges": ["+/- 10 V"], "bias_range_index": 0})
    client.script("Signals.NamesGet", {"signals_names": ["I", "Bias", "Z"]})
    client.script("BiasSpectr.StatusGet", 0)
    client.script("Bias.Get", 0.2, 0.3)
    client.script("ZCtrl.SetpntGet", 1e-10)
    client.script("ZCtrl.OnOffGet", 1)
    client.script("BiasSpectr.ChsGet", chs(), chs())
    client.script(
        "BiasSpectr.PropsGet",
        props(),
        props(points=3, sweeps=1, backward=0, save_all=0),
    )
    client.script("BiasSpectr.LimitsGet", limits(), limits(-1, 1))
    client.script("BiasSpectr.TimingGet", timing(), timing())
    client.script("BiasSpectr.AdvPropsGet", advanced(), advanced())
    client.script("BiasSpectr.Start", start_response() if start is None else start)
    return client


def test_invalid_config_and_policy_bounds_send_nothing():
    client = RecoverableFakeController()
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())
    with pytest.raises(SafetyPreflightError):
        workflow.run(config(start_voltage=-3))
    assert client.sent == []


@pytest.mark.parametrize(
    "changes",
    [
        {"recovery_timeout": 0},
        {"status_poll_interval": 0},
        {"recovery_timeout": 1, "status_poll_interval": 2},
        {"maximum_slew_rate": float("nan")},
        {"z_offset": float("inf")},
    ],
)
def test_structural_and_recovery_timing_validation(changes):
    with pytest.raises(ValueError):
        config(**changes)


def test_snapshot_patch_readback_start_and_reverse_restore_order():
    client = scripted_controller()
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())

    result = workflow.run(config())

    commands = [command for command, _, _ in client.sent]
    assert result.effective_settings.points == 3
    assert commands.index("BiasSpectr.Open") < commands.index("BiasSpectr.ChsGet")
    first_chs_set = commands.index("BiasSpectr.ChsSet")
    assert commands[first_chs_set : first_chs_set + 4] == [
        "BiasSpectr.ChsSet",
        "BiasSpectr.PropsSet",
        "BiasSpectr.LimitsSet",
        "BiasSpectr.TimingSet",
    ]
    start_index = commands.index("BiasSpectr.Start")
    # Settings restore begins before tip feedback/bias restoration.
    assert commands.index("BiasSpectr.AdvPropsSet", start_index) < commands.index(
        "ZCtrl.OnOffSet", start_index
    )
    start_call = client.sent[start_index]
    assert start_call[2] is not None and start_call[2] > 5
    assert result.acquisition_timeout_used == start_call[2]


def test_none_overrides_preserve_existing_and_one_z_offset_goes_to_both_setters():
    client = scripted_controller()
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())

    workflow.run(config(z_offset=5e-9))

    props_set = next(args for cmd, args, _ in client.sent if cmd == "BiasSpectr.PropsSet")
    timing_set = next(args for cmd, args, _ in client.sent if cmd == "BiasSpectr.TimingSet")
    assert props_set[4] == pytest.approx(5e-9)
    assert timing_set[1] == pytest.approx(5e-9)
    assert timing_set[5] == pytest.approx(0.02)


def test_explicit_acquisition_timeout_is_used():
    client = scripted_controller()
    result = BiasSpectroscopyWorkflow(client, safety_policy=safety()).run(
        config(acquisition_timeout=123)
    )
    call = next(entry for entry in client.sent if entry[0] == "BiasSpectr.Start")
    assert call[2] == 123
    assert result.acquisition_timeout_used == 123


def test_start_timeout_reconnects_stops_waits_then_restores():
    client = scripted_controller()
    client._responses["BiasSpectr.Start"].clear()
    client.fail("BiasSpectr.Start", NanonisTimeoutError("late"))
    # Preflight consumed the first status; recovery sees running, then stopped.
    client.script("BiasSpectr.StatusGet", 1, 0)
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())

    with pytest.raises(NanonisTimeoutError):
        workflow.run(config())

    commands = [entry[0] for entry in client.sent]
    stop = commands.index("BiasSpectr.Stop")
    restored = commands.index("BiasSpectr.ChsSet", commands.index("BiasSpectr.Start"))
    assert client.reconnect_count == 1
    assert stop < restored


def test_failed_recovery_raises_state_error_and_performs_no_restoration():
    client = scripted_controller()
    client._responses["BiasSpectr.Start"].clear()
    client.fail("BiasSpectr.Start", NanonisTimeoutError("late"))
    client.reconnect_error = RuntimeError("offline")
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())

    with pytest.raises(StateRestorationError) as caught:
        workflow.run(config())

    assert isinstance(caught.value.original_error, NanonisTimeoutError)
    start_index = next(i for i, entry in enumerate(client.sent) if entry[0] == "BiasSpectr.Start")
    assert not any(
        command in {"BiasSpectr.ChsSet", "Bias.Set", "ZCtrl.SetpntSet"}
        for command, _, _ in client.sent[start_index + 1 :]
    )


def test_preflight_is_mandatory_unless_explicitly_skipped():
    client = scripted_controller()
    client._responses["Bias.RangeGet"].clear()
    client.script("Bias.RangeGet", {"bias_ranges": ["mystery"], "bias_range_index": 0})
    workflow = BiasSpectroscopyWorkflow(client, safety_policy=safety())
    with pytest.raises(SafetyPreflightError):
        workflow.run(config())
    assert not any(command == "BiasSpectr.Start" for command, _, _ in client.sent)

    skipped = scripted_controller()
    result = BiasSpectroscopyWorkflow(skipped, safety_policy=safety()).run(
        config(), unsafe_skip_preflight=True
    )
    assert result.data.shape == (2, 3)
    assert not any(command == "Bias.RangeGet" for command, _, _ in skipped.sent)


def test_preflight_uses_policy_bound_for_non_switchable_bias_range(caplog):
    client = scripted_controller()
    client._responses["Bias.RangeGet"].clear()
    client.script(
        "Bias.RangeGet",
        {"bias_ranges": ["Not switchable"], "bias_range_index": 0},
    )

    preflight_bias_spectroscopy(client, config(), safety())

    assert "using the safety-policy bound" in caplog.text


@pytest.mark.parametrize(
    ("description", "bounds"),
    [
        ("+/- 10 V", (-10, 10)),
        ("±500 mV", (-0.5, 0.5)),
        ("-2 V to 3 V", (-2, 3)),
    ],
)
def test_bias_range_parser(description, bounds):
    assert parse_bias_range(description) == pytest.approx(bounds)


def test_zero_slew_rate_does_not_divide_by_zero(caplog):
    client = scripted_controller()
    # Build a settings object through the same typed snapshot path.
    client._responses["BiasSpectr.TimingGet"].clear()
    client.script("BiasSpectr.TimingGet", timing(slew=0))
    settings = __import__(
        "nanonis.workflows", fromlist=["BiasSpectroscopySettings"]
    ).BiasSpectroscopySettings.snapshot(client)
    assert estimate_acquisition_duration(settings) >= 60
    assert "slew-limited" in caplog.text
