from datetime import datetime, timezone

import numpy as np
import pytest

from nanonis.qcodes.spectroscopy import (
    add_bias_spectroscopy_result,
    register_bias_spectroscopy,
)
from nanonis.qcodes.scan import add_scan_result, register_scan_result
from nanonis.workflows import (
    BiasSpectroscopyAdvanced,
    BiasSpectroscopyConfig,
    BiasSpectroscopySettings,
    BiasSpectroscopyTiming,
)
from nanonis.workflows.scan import ScanChannelImage, ScanConfig, normalize_scan
from nanonis.workflows.spectroscopy.result import BiasSpectroscopyResult

from .scan.test_models import snapshot


class FakeMeasurement:
    def __init__(self):
        self.registered = []

    def register_custom_parameter(self, name, **kwargs):
        self.registered.append((name, kwargs))
        return self


class FakeDataset:
    def __init__(self):
        self.metadata = {}

    def add_metadata(self, key, value):
        self.metadata[key] = value


class FakeDataSaver:
    def __init__(self):
        self.dataset = FakeDataset()
        self.results = []

    def add_result(self, *pairs):
        self.results.append(pairs)


def result(*, backward=False, columns=3):
    cfg = BiasSpectroscopyConfig(-1, 1, 3, (0, 1), include_backward=backward)
    effective = BiasSpectroscopySettings(
        channels=(0, 1),
        save_all=False,
        sweeps=1,
        include_backward=backward,
        points=3,
        autosave=False,
        show_save_dialog=False,
        timing=BiasSpectroscopyTiming(0.1, 0, 0.1, 1, 0.1, 0.1, 0.1, 0.1),
        advanced=BiasSpectroscopyAdvanced(False, True, False, False),
        limits=(-1, 1),
    )
    now = datetime.now(timezone.utc)
    return BiasSpectroscopyResult(
        channel_names=("Current (A)", "Current (A)"),
        data=np.arange(2 * columns).reshape(2, columns),
        data_rows=2,
        data_columns=columns,
        parameters=(),
        requested_config=cfg,
        effective_settings=effective,
        acquisition_started_at=now,
        acquisition_finished_at=now,
        acquisition_duration=0,
        estimated_acquisition_duration=1,
        acquisition_timeout_used=6,
    )


def test_sample_index_always_present_and_identifiers_are_unique():
    measurement = FakeMeasurement()

    registered = register_bias_spectroscopy(measurement, result(backward=True))

    assert registered.sample_index_name == "sample_index"
    assert registered.voltage_name is None
    assert [trace.parameter_name for trace in registered.traces] == [
        "current_a",
        "current_a_2",
    ]
    assert [trace.label for trace in registered.traces] == [
        "Current (A)",
        "Current (A)",
    ]
    for _, kwargs in measurement.registered[1:]:
        assert kwargs["setpoints"] == ("sample_index",)


def test_voltage_setpoint_is_only_added_for_forward_matching_shape():
    forward_measurement = FakeMeasurement()
    forward = register_bias_spectroscopy(forward_measurement, result())
    mismatch = register_bias_spectroscopy(FakeMeasurement(), result(columns=4))
    backward = register_bias_spectroscopy(FakeMeasurement(), result(backward=True))

    assert forward.voltage_name == "configured_voltage"
    assert mismatch.voltage_name is None
    assert backward.voltage_name is None
    trace_registration = forward_measurement.registered[-1][1]
    assert trace_registration["setpoints"] == (
        "sample_index",
        "configured_voltage",
    )


def test_add_result_writes_axes_traces_and_acquisition_metadata():
    value = result()
    registered = register_bias_spectroscopy(FakeMeasurement(), value)
    datasaver = FakeDataSaver()

    add_bias_spectroscopy_result(datasaver, registered, value)

    pairs = dict(datasaver.results[0])
    assert pairs["sample_index"].tolist() == [0, 1, 2]
    assert pairs["configured_voltage"].tolist() == [-1, 0, 1]
    assert pairs["current_a"].tolist() == [0, 1, 2]
    assert "acquisition_started_at" in datasaver.dataset.metadata
    assert "effective_settings" in datasaver.dataset.metadata


def scan_result():
    """A 3x4 (lines x pixels) result with two images (ch0 forward + backward)."""
    effective, _ = snapshot()  # frame 10x20 nm, angle 5 deg; pixels=4, lines=3
    now = datetime.now(timezone.utc)
    forward = ScanChannelImage("Current (A)", 0, "forward",
                               np.arange(12.0).reshape(3, 4), "up")
    backward = ScanChannelImage("Current (A)", 0, "backward",
                                np.arange(12.0, 24.0).reshape(3, 4), "down")
    return normalize_scan(
        (forward, backward), saved_path="scan.sxm", config=ScanConfig((0,)),
        effective=effective, acquisition_started_at=now,
        acquisition_finished_at=now, acquisition_duration=1,
        estimated_acquisition_duration=2, acquisition_timeout_used=8,
    )


def test_scan_registers_index_setpoints_coordinates_and_unique_channel_ids():
    measurement = FakeMeasurement()

    registered = register_scan_result(measurement, scan_result())

    assert registered.shape == (3, 4)
    assert (registered.x_name, registered.y_name) == ("x_m", "y_m")
    assert [c.parameter_name for c in registered.channels] == [
        "current_a_forward",
        "current_a_backward",
    ]
    registered_params = dict(measurement.registered)
    # Index setpoints are independent (no setpoints of their own).
    assert "setpoints" not in registered_params["row_index"]
    assert "setpoints" not in registered_params["col_index"]
    # Every image and coordinate grid hangs off the 2-D index meshgrids.
    for name in ("x_m", "y_m", "current_a_forward", "current_a_backward"):
        assert registered_params[name]["setpoints"] == ("row_index", "col_index")
    assert registered_params["current_a_forward"]["unit"] == "A"


def test_physical_coordinates_can_be_disabled():
    measurement = FakeMeasurement()

    registered = register_scan_result(
        measurement, scan_result(), physical_coordinates=False
    )

    assert registered.x_name is None and registered.y_name is None
    assert "x_m" not in dict(measurement.registered)


def test_add_scan_result_writes_grids_images_and_metadata():
    value = scan_result()
    registered = register_scan_result(FakeMeasurement(), value)
    datasaver = FakeDataSaver()

    add_scan_result(datasaver, registered, value)

    pairs = dict(datasaver.results[0])
    assert pairs["row_index"].shape == (3, 4)
    assert pairs["col_index"].shape == (3, 4)
    # Index meshgrids: row varies down rows, column across columns.
    assert pairs["row_index"][:, 0].tolist() == [0, 1, 2]
    assert pairs["col_index"][0, :].tolist() == [0, 1, 2, 3]
    assert pairs["x_m"].shape == (3, 4) and pairs["y_m"].shape == (3, 4)
    assert pairs["current_a_forward"][0].tolist() == [0, 1, 2, 3]
    assert pairs["current_a_backward"][0].tolist() == [12, 13, 14, 15]
    assert datasaver.dataset.metadata["row_order"] == "top_to_bottom"
    for key in ("acquisition_started_at", "saved_path", "frame", "effective_settings"):
        assert key in datasaver.dataset.metadata


def test_add_scan_result_rejects_channel_schema_mismatch():
    value = scan_result()
    registered = register_scan_result(FakeMeasurement(), value)
    only_forward = value.images[0]
    partial = scan_result()
    object.__setattr__(partial, "images", (only_forward,))

    with pytest.raises(ValueError, match="schema does not match"):
        add_scan_result(FakeDataSaver(), registered, partial)
