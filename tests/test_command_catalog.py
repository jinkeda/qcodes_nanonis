"""Regression coverage for the complete Nanonis command catalog."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import generate_nanonis_tcp as generator
from nanonis.command import CommandRegistry
from nanonis.command.registry import convert_raw_args


ROOT = Path(__file__).parents[1]
CONFIG_DIR = ROOT / "configs" / "commands"
MANIFEST = Path(__file__).parent / "fixtures" / "command_schema_manifest.json"
MANUAL = ROOT / "TCPProtocol_SPM.pdf"


def registry() -> CommandRegistry:
    result = CommandRegistry()
    result.load_from_dir(CONFIG_DIR)
    return result


def test_complete_catalog_matches_schema_manifest():
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
    commands = registry()

    assert expected["manual_revision"] == "April 2025 R14718"
    assert len(commands.list_commands()) == expected["command_count"] == 661
    assert len(commands.list_modules()) == expected["module_count"] == 57
    assert set(commands.list_commands()) == set(expected["commands"])

    for name, schema in expected["commands"].items():
        assert commands.get(name).get_send_types() == [
            tuple(value) for value in schema["send"]
        ]
        assert commands.get(name).get_recv_types() == [
            tuple(value) for value in schema["recv"]
        ]


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="Poppler unavailable")
def test_catalog_wire_shapes_match_protocol_manual():
    manual = generator.parse_pdf(MANUAL)
    commands = registry()

    assert len(manual) == 661
    assert set(manual) == set(commands.list_commands())
    for name, raw in manual.items():
        expected_send = [value["type"] for value in convert_raw_args(raw["args"])]
        expected_recv = [value["type"] for value in convert_raw_args(raw["resp"])]
        assert [value.type for value in commands.get(name).send_args] == expected_send
        assert [value.type for value in commands.get(name).recv_args] == expected_recv


def test_repaired_command_shapes_are_pinned():
    commands = registry()

    assert commands.get("MProbeCurrent.Get").get_send_types() == [
        ("scanner_index", "uint16")
    ]
    assert commands.get("MProbeCurrent.Get").get_recv_types() == [
        ("current_value_a", "float32")
    ]
    assert commands.get("PLLPhasSwp.Stop").get_send_types() == [
        ("modulator_index", "int32")
    ]
    assert commands.get("PLLPhasSwp.Stop").recv_args == []
    assert commands.get("PLLQCtrl.PhaseGet").send_args == []
    assert commands.get("PLLQCtrl.PhaseGet").get_recv_types() == [
        ("phase_adjustment", "int32"),
        ("phase_custom", "float32"),
    ]
    assert commands.get("Piezo.DriftCompSet").send_args[0].type == "int32"
    assert commands.get("Util.SessionPathGet").get_recv_types() == [
        ("session_path", "string")
    ]


def test_generator_handles_manual_type_edge_cases():
    assert generator.parse_bullet(
        "- Bias end (V) (1D array float32 is the end value"
    ) == ("Bias end (V)", "1D array float32")
    assert generator.parse_bullet(
        "- Digital lines (1D array unsigned int8) defines the outputs"
    ) == ("Digital lines", "1D array unsigned int8")
