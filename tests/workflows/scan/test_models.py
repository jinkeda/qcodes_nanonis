from dataclasses import replace

import pytest

from nanonis.workflows import BiasRestoreMode, TipRestorePolicy
from nanonis.workflows.scan import (
    ScanConfig,
    ScanSettings,
    decode_keep_constant_get,
    decode_on_off_get,
    decode_save_mode_get,
    encode_keep_constant_set,
    encode_on_off_set,
    encode_save_mode_set,
)

from ..conftest import FakeController


def frame():
    return {"center_x_m": 0, "center_y_m": 0, "width_m": 1e-8,
            "height_m": 2e-8, "angle_deg": 5}


def buffer():
    return {"num_channels": 1, "channel_indexes": [0], "pixels": 4, "lines": 3}


def props(*, continuous=1):
    return {
        "continuous_scan": continuous,
        "bouncy_scan": 0,
        "autosave": 1,
        "series_name": "old",
        "comment": "note",
        "modules_names": ["Scan"],
        "num_parameters_per_module_array": [2],
        "parameters": [["A", "B"]],
        "autopaste": 2,
    }


def speed():
    return {
        "forward_linear_speed_m_s": 1e-7,
        "backward_linear_speed_m_s": 2e-7,
        "forward_time_per_line_s": 0.01,
        "backward_time_per_line_s": 0.02,
        "keep_parameter_constant": 0,
        "speed_ratio": 2,
    }


def snapshot():
    client = FakeController()
    client.script("Scan.FrameGet", frame())
    client.script("Scan.BufferGet", buffer())
    client.script("Scan.PropsGet", props())
    client.script("Scan.SpeedGet", speed())
    return ScanSettings.snapshot(client), client


def test_asymmetric_get_set_conversions_round_trip():
    assert [encode_on_off_set(decode_on_off_get(value)) for value in (0, 1)] == [2, 1]
    assert [encode_save_mode_set(decode_save_mode_get(value)) for value in range(3)] == [1, 2, 3]
    assert [encode_keep_constant_set(decode_keep_constant_get(value)) for value in (0, 1)] == [1, 2]
    assert encode_on_off_set(None) == 0
    assert encode_save_mode_set(None) == 0
    assert encode_keep_constant_set(None) == 0


def test_snapshot_patch_preserves_none_and_forces_continuous_off():
    original, _ = snapshot()
    desired = original.patch(
        ScanConfig((0,), forward_line_time=0.03, series_name="new")
    )

    assert desired.frame == original.frame
    assert desired.speed.backward_time_per_line == original.speed.backward_time_per_line
    assert desired.speed.forward_time_per_line == 0.03
    assert desired.speed.keep_parameter_constant == "time_per_line"
    assert desired.props.continuous is False
    assert desired.props.series_name == "new"
    assert desired.props.parameters == (("A", "B"),)


def test_apply_order_and_restore_encoding():
    settings, client = snapshot()
    assert settings.apply(client) == {}
    calls = client.sent[4:]
    assert [entry[0] for entry in calls] == [
        "Scan.FrameSet", "Scan.BufferSet", "Scan.SpeedSet", "Scan.PropsSet"
    ]
    assert calls[-1][1][0:3] == (1, 2, 2)  # on, off, autosave next


def test_config_rejects_boolean_autosave_and_tip_policy_is_shared():
    with pytest.raises(ValueError):
        ScanConfig((0,), autosave=True)
    policy = TipRestorePolicy(BiasRestoreMode.DIRECT, None, True)
    assert policy.bias_restore_mode is BiasRestoreMode.DIRECT


@pytest.mark.parametrize("changes", [
    {"pixels": 1}, {"lines": 1}, {"channel_indexes": (0, 0)},
    {"width": 0}, {"forward_line_time": float("nan")},
])
def test_invalid_config(changes):
    with pytest.raises(ValueError):
        replace(ScanConfig((0,)), **changes)
