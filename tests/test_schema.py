"""Regression tests for the BiasSpectr command definitions."""

import struct
from pathlib import Path

from nanonis.command import CommandDecoder, CommandEncoder, CommandRegistry


CONFIG_DIR = Path(__file__).parents[1] / "configs" / "commands"


def registry() -> CommandRegistry:
    value = CommandRegistry()
    value.load_from_dir(CONFIG_DIR)
    return value


def test_propsget_runtime_recv_names():
    names = [
        name for name, _ in registry().get("BiasSpectr.PropsGet").get_recv_types()
    ]
    assert names == [
        "save_all",
        "num_sweeps",
        "backward_sweep",
        "num_points",
        "parameters_size",
        "num_parameters",
        "parameters",
        "fixed_parameters_size",
        "num_fixed_parameters",
        "fixed_parameters",
        "autosave",
        "show_save_dialog",
    ]


def test_propsget_binary_fixture_trailer_is_at_the_correct_offset():
    types = registry().get("BiasSpectr.PropsGet").get_recv_types()
    varying = ["Start bias (V)", "End bias (V)"]
    fixed = ["Z offset (m)"]
    values = (
        1,
        3,
        0,
        8,
        sum(4 + len(item.encode()) for item in varying),
        len(varying),
        varying,
        sum(4 + len(item.encode()) for item in fixed),
        len(fixed),
        fixed,
        1,
        0,
    )
    body = CommandEncoder().encode(types, values) + struct.pack(">Ii", 0, 0)

    decoded = CommandDecoder().decode(
        types, body, check_error=True, command_name="BiasSpectr.PropsGet"
    )

    assert decoded["fixed_parameters"] == fixed
    assert decoded["autosave"] == 1
    assert decoded["show_save_dialog"] == 0


def test_propsset_and_new_setter_shapes_match_the_manual():
    commands = registry()
    assert len(commands.get("BiasSpectr.PropsSet").send_args) == 7
    assert len(commands.get("BiasSpectr.TimingSet").send_args) == 8
    assert len(commands.get("BiasSpectr.AdvPropsSet").send_args) == 4
    assert len(commands.get("BiasSpectr.LimitsSet").send_args) == 2
    assert commands.get("BiasSpectr.Stop").send_args == []
    assert commands.get("BiasSpectr.StatusGet").get_recv_types() == [
        ("status", "uint32")
    ]


def test_scan_setters_and_piezo_range_match_the_manual():
    commands = registry()
    assert [value.type for value in commands.get("Scan.FrameSet").send_args] == [
        "float32"
    ] * 5
    expected_speed = [
        "float32",
        "float32",
        "float32",
        "float32",
        "uint16",
        "float32",
    ]
    assert [value.type for value in commands.get("Scan.SpeedSet").send_args] == expected_speed
    assert [value.type for value in commands.get("Scan.SpeedGet").recv_args] == expected_speed
    assert commands.get("Scan.BufferGet").get_recv_types()[-2:] == [
        ("pixels", "int32"),
        ("lines", "int32"),
    ]
    assert commands.get("Piezo.RangeGet").get_recv_types() == [
        ("range_x_m", "float32"),
        ("range_y_m", "float32"),
        ("range_z_m", "float32"),
    ]


def test_z_spectroscopy_commands_match_the_manual():
    commands = registry()
    expected = {
        "ZSpectr.Open",
        "ZSpectr.Start",
        "ZSpectr.Stop",
        "ZSpectr.StatusGet",
        "ZSpectr.ChsSet",
        "ZSpectr.ChsGet",
        "ZSpectr.PropsSet",
        "ZSpectr.PropsGet",
        "ZSpectr.AdvPropsSet",
        "ZSpectr.AdvPropsGet",
        "ZSpectr.RangeSet",
        "ZSpectr.RangeGet",
        "ZSpectr.TimingSet",
        "ZSpectr.TimingGet",
        "ZSpectr.RetractDelaySet",
        "ZSpectr.RetractDelayGet",
        "ZSpectr.RetractSet",
        "ZSpectr.RetractGet",
        "ZSpectr.Retract2ndSet",
        "ZSpectr.Retract2ndGet",
        "ZSpectr.DigSyncSet",
        "ZSpectr.DigSyncGet",
        "ZSpectr.TTLSyncSet",
        "ZSpectr.TTLSyncGet",
        "ZSpectr.PulseSeqSyncSet",
        "ZSpectr.PulseSeqSyncGet",
    }
    assert set(commands.list_commands("ZSpectr.")) == expected

    # Scalar strings include their own length on the wire, so the registry
    # normalizes away the manual's redundant Save-base-name-size field.
    assert commands.get("ZSpectr.Start").get_send_types() == [
        ("get_data", "uint32"),
        ("save_base_name", "string"),
    ]
    assert [
        value.type for value in commands.get("ZSpectr.AdvPropsSet").send_args
    ] == ["float32", "uint16", "uint16", "uint16"]
    assert [
        value.name for value in commands.get("ZSpectr.AdvPropsSet").send_args
    ] == [
        "time_between_forward_and_backward_sweep_s",
        "record_final_z",
        "lockin_run",
        "reset_z",
    ]
    assert commands.get("ZSpectr.StatusGet").get_recv_types() == [
        ("status", "uint32")
    ]
    assert commands.get("ZSpectr.Stop").send_args == []


def test_decoder_rejects_missing_or_incomplete_error_trailer():
    decoder = CommandDecoder()
    types = [("value", "float32")]
    value = struct.pack(">f", 1.0)

    for body in (value, value + b"\0" * 7, value + struct.pack(">Ii", 0, 1)):
        try:
            decoder.decode(types, body, check_error=True)
        except Exception as exc:
            assert "trailer" in str(exc).lower()
        else:
            raise AssertionError("malformed response was accepted")

