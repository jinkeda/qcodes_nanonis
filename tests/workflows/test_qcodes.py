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
from nanonis.workflows.spectroscopy.result import BiasSpectroscopyResult


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


def test_scan_persistence_seam_is_explicitly_deferred():
    with pytest.raises(NotImplementedError, match="deferred"):
        register_scan_result(None, None)
    with pytest.raises(NotImplementedError, match="deferred"):
        add_scan_result(None, None, None)
