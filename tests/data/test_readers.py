from pathlib import Path

import numpy as np
import pytest

from nanonis.data import read_3ds, read_dat, read_session, read_sxm
from nanonis.data.readers._parser import parse_file
from nanonis.types import NaNPolicy

EXAMPLES = Path(__file__).parents[2] / "data_example"


def test_sxm_fixture_matches_low_level_parser():
    path = EXAMPLES / "FGT_0030.sxm"
    raw, _ = parse_file("sxm", path)
    data = read_sxm(path, nan_policy=NaNPolicy.RAISE)

    assert (data.pixels, data.lines) == (256, 256)
    assert data.scan_direction == "down"
    assert data.region.angle == 90.0
    assert len(data.channels) == 4
    for channel in data.channels:
        assert channel.directions == ("forward", "backward")
        np.testing.assert_array_equal(channel.forward, raw.signals[channel.name]["forward"])
        np.testing.assert_array_equal(channel.backward, raw.signals[channel.name]["backward"])
        assert not channel.forward.flags.writeable
    metadata = data.to_metadata()
    assert metadata["controller"] == {
        "nanonis_version": "2",
        "software_version": "Generic 5",
    }
    assert metadata["software"]["git_commit"]
    assert "header" not in metadata
    assert "header" in data.to_metadata(include_header=True)


def test_3ds_fixture_matches_low_level_parser():
    path = EXAMPLES / "Grid Spectroscopy023.3ds"
    raw, _ = parse_file("3ds", path)
    data = read_3ds(path, nan_policy=NaNPolicy.ALLOW)

    assert (data.lines, data.pixels) == (64, 64)
    assert data.sweep_signal.values.shape == (101,)
    assert data.sweep_signal.direction == "decreasing"
    assert len(data.channels) == 6
    np.testing.assert_array_equal(data.channels[0].values, raw.signals["Current (A)"])
    np.testing.assert_array_equal(data.sweep_signal.values, raw.signals["sweep_signal"])
    assert len(data.fixed_parameters) == 14


def test_dat_fixture_matches_low_level_parser():
    path = EXAMPLES / "Bias-Spectroscopy_00146.dat"
    raw, _ = parse_file("dat", path)
    data = read_dat(path, nan_policy=NaNPolicy.ALLOW)

    assert data.points == 201
    assert len(data.columns) == 13
    np.testing.assert_array_equal(data.columns[0].values, raw.signals["Bias calc (V)"])
    assert data.to_metadata()["parser"]["name"] in {"nanonispy", "nanonispy2"}


def test_truncated_sxm_is_rejected(tmp_path):
    original = (EXAMPLES / "FGT_0030.sxm").read_bytes()
    path = tmp_path / "short.sxm"
    path.write_bytes(original[:-128])
    with pytest.raises(Exception, match="expected|payload|truncated|corrupt"):
        read_sxm(path)


def test_session_reader_exposes_typed_measurement_modules():
    session = read_session(EXAMPLES / "Nanonis-Session.ini")
    assert len(session.modules) >= 30
    assert session.lock_in is not None
    assert session.atom_tracking is not None
    assert session.bias_spectroscopy is not None
    assert isinstance(session.lock_in.values, dict) is False
