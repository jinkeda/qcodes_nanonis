"""Constraint-driven validation for variable-length command fields."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from nanonis.command import (
    CommandDecoder,
    CommandEncoder,
    CommandRegistry,
    NanonisArgumentError,
    NanonisController,
)
from nanonis.protocol import NanonisProtocolError


CONFIG_DIR = Path(__file__).parents[1] / "configs" / "commands"


def registry() -> CommandRegistry:
    value = CommandRegistry()
    value.load_from_dir(CONFIG_DIR)
    return value


def test_constraint_overlay_has_complete_catalog_coverage():
    commands = registry()
    send = [c for c in commands.list_commands() if commands.get(c).send_constraints]
    recv = [c for c in commands.list_commands() if commands.get(c).recv_constraints]
    recv_fields = sum(len(commands.get(c).recv_constraints) for c in recv)
    matrices = sum(
        constraint.rows is not None
        for command in recv
        for constraint in commands.get(command).recv_constraints.values()
    )

    assert len(send) == 19
    assert len(recv) == 57
    assert recv_fields == 108
    assert matrices == 13


@patch("nanonis.command.controller.NanonisTCPClient")
def test_positional_mismatch_is_rejected_before_send(mock_client_class):
    client = MagicMock()
    mock_client_class.return_value = client
    controller = NanonisController("127.0.0.1", 6501, CONFIG_DIR)

    with pytest.raises(NanonisArgumentError, match="num_channels"):
        controller.send("Scan.BufferSet", 3, [0, 1], 256, 256)

    client.send_raw.assert_not_called()


@patch("nanonis.command.controller.NanonisTCPClient")
def test_named_fields_infer_count_and_send(mock_client_class):
    client = MagicMock()
    client.send_raw.return_value = struct.pack(">Ii", 0, 0)
    mock_client_class.return_value = client
    controller = NanonisController("127.0.0.1", 6501, CONFIG_DIR)

    controller.send_fields(
        "Scan.BufferSet",
        channel_indexes=[0, 1],
        pixels=256,
        lines=128,
    )

    expected = (
        struct.pack(">i", 2)
        + np.asarray([0, 1], dtype=">i4").tobytes()
        + struct.pack(">ii", 256, 128)
    )
    client.send_raw.assert_called_once_with("Scan.BufferSet", expected)


@patch("nanonis.command.controller.NanonisTCPClient")
def test_shared_count_requires_all_parallel_arrays_to_match(mock_client_class):
    client = MagicMock()
    mock_client_class.return_value = client
    controller = NanonisController("127.0.0.1", 6501, CONFIG_DIR)

    with pytest.raises(NanonisArgumentError, match="start_point_y_coordinate_m"):
        controller.send(
            "Marks.LinesDraw",
            2,
            [0.0, 1.0],
            [0.0],
            [1.0, 2.0],
            [1.0, 2.0],
            [0, 0],
        )

    client.send_raw.assert_not_called()


@patch("nanonis.command.controller.NanonisTCPClient")
def test_named_string_array_infers_utf8_wire_size(mock_client_class):
    client = MagicMock()
    client.send_raw.return_value = struct.pack(">Ii", 0, 0)
    mock_client_class.return_value = client
    controller = NanonisController("127.0.0.1", 6501, CONFIG_DIR)

    controller.send_fields(
        "HSSwp.SaveOptionsSet",
        comment="test",
        modules_names=["Scan", "日本語"],
    )

    body = client.send_raw.call_args.args[1]
    comment_size = 4 + len("test".encode("utf-8"))
    expected_array_size = 4 + 4 + 4 + len("日本語".encode("utf-8"))
    assert struct.unpack(">i", body[comment_size : comment_size + 4])[0] == expected_array_size
    assert struct.unpack(">i", body[comment_size + 4 : comment_size + 8])[0] == 2


@patch("nanonis.command.controller.NanonisTCPClient")
def test_generator_input_is_materialized_once(mock_client_class):
    client = MagicMock()
    client.send_raw.return_value = struct.pack(">iIi", 0, 0, 0)
    mock_client_class.return_value = client
    controller = NanonisController("127.0.0.1", 6501, CONFIG_DIR)

    controller.send_fields(
        "Signals.ValsGet",
        signals_indexes=(value for value in [1, 2, 3]),
        wait_for_newest_data=1,
    )

    body = client.send_raw.call_args.args[1]
    assert struct.unpack(">i", body[:4])[0] == 3
    np.testing.assert_array_equal(
        np.frombuffer(body[4:16], dtype=">i4"), [1, 2, 3]
    )


def test_encoder_rejects_wrong_array_dimension():
    with pytest.raises(ValueError, match="one-dimensional"):
        CommandEncoder().encode(
            [("values", "array_float32")],
            (np.ones((2, 2), dtype=np.float32),),
        )


def test_marks_points_get_uses_point_count_for_every_array():
    command = registry().get("Marks.PointsGet")
    texts = ["A", "日本語"]
    values = (
        2,
        [1.0, 2.0],
        [3.0, 4.0],
        CommandEncoder.encoded_string_array_size(texts),
        texts,
        [0x112233, 0x445566],
        [1, 0],
    )
    body = CommandEncoder().encode(command.get_recv_types(), values)
    body += struct.pack(">Ii", 0, 0)

    decoded = CommandDecoder().decode(
        command.get_recv_types(),
        body,
        check_error=True,
        command_name=command.name,
        constraints=command.recv_constraints,
    )

    assert decoded["text"] == texts
    np.testing.assert_array_equal(decoded["color"], [0x112233, 0x445566])
    np.testing.assert_array_equal(decoded["visible"], [1, 0])


def test_response_string_array_byte_size_is_checked():
    command = registry().get("Marks.PointsGet")
    values = (1, [1.0], [2.0], 999, ["A"], [0], [1])
    body = CommandEncoder().encode(command.get_recv_types(), values)
    body += struct.pack(">Ii", 0, 0)

    with pytest.raises(NanonisProtocolError, match="declares 999"):
        CommandDecoder().decode(
            command.get_recv_types(),
            body,
            check_error=True,
            command_name=command.name,
            constraints=command.recv_constraints,
        )


def test_overlay_rejects_partial_command_constraints(tmp_path):
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "Test.json").write_text(
        json.dumps(
            {
                "Test.Get": {
                    "args": [],
                    "resp": [
                        {"name": "Count", "type": "i"},
                        {"name": "First", "type": "1D array int"},
                        {"name": "Second", "type": "1D array int"},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "command_constraints.json").write_text(
        json.dumps(
            {"Test.Get": {"recv": {"first": {"count": "count"}}}}
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cover the whole side"):
        CommandRegistry().load_from_dir(command_dir)


def test_registry_rejects_sanitized_name_collision(tmp_path):
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "Test.json").write_text(
        json.dumps(
            {
                "Test.Set": {
                    "args": [
                        {"name": "A-B", "type": "i"},
                        {"name": "A B", "type": "i"},
                    ],
                    "resp": [],
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not unique after sanitization"):
        CommandRegistry().load_from_dir(command_dir)
