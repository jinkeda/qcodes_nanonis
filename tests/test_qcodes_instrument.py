# -*- coding: utf-8 -*-
"""
Tests for QCoDeS Nanonis integration.
"""

from unittest.mock import Mock

import pytest

pytest.importorskip("qcodes")

from qcodes import Station

from nanonis.qcodes.instrument import NanonisInstrument


class DummyController:
    def __init__(self, host, port, config_path, timeout):
        self.host = host
        self.port = port
        self.config_path = config_path
        self.timeout = timeout
        self._connected = False
        self._bias_voltage = 0.0
        self._scan_frame = {
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 100e-9,
            "height": 100e-9,
            "angle": 0.0,
        }
        self.connect = Mock(side_effect=self._connect)
        self.disconnect = Mock(side_effect=self._disconnect)
        self.send = Mock(side_effect=self._send)
        self.list_commands = Mock(return_value=["Bias.Get", "Scan.FrameGet"])
        self.list_modules = Mock(return_value=["Bias", "Scan"])

    @property
    def is_connected(self):
        return self._connected

    def _connect(self):
        self._connected = True

    def _disconnect(self):
        self._connected = False

    def _send(self, command, *args):
        if command == "Bias.Get":
            return self._bias_voltage
        if command == "Bias.Set":
            self._bias_voltage = args[0]
            return None
        if command == "Scan.FrameGet":
            return dict(self._scan_frame)
        if command == "Scan.FrameSet":
            (
                self._scan_frame["center_x"],
                self._scan_frame["center_y"],
                self._scan_frame["width"],
                self._scan_frame["height"],
                self._scan_frame["angle"],
            ) = args
            return None
        if command == "Scan.Action":
            return None
        return None


@pytest.fixture
def instrument(monkeypatch):
    from nanonis.qcodes import instrument as instrument_module

    monkeypatch.setattr(instrument_module, "NanonisController", DummyController)
    inst = NanonisInstrument(
        "nanonis",
        host="127.0.0.1",
        port=6501,
        config_path="configs/nanonis_tcp.yaml",
    )
    yield inst
    inst.close()


def test_instrument_initializes_channels(instrument):
    assert instrument.controller.is_connected
    assert instrument.bias is not None
    assert instrument.scan is not None


def test_bias_voltage_get_set(instrument):
    instrument.bias.voltage(0.5)
    instrument.controller.send.assert_any_call("Bias.Set", 0.5)
    assert instrument.bias.voltage() == 0.5
    instrument.controller.send.assert_any_call("Bias.Get")


def test_scan_frame_parameters(instrument):
    instrument.scan.set_frame(1e-9, 2e-9, 3e-9, 4e-9, 5.0)
    instrument.controller.send.assert_any_call(
        "Scan.FrameSet", 1e-9, 2e-9, 3e-9, 4e-9, 5.0
    )
    assert instrument.scan.width() == 3e-9
    assert instrument.scan.height() == 4e-9
    instrument.controller.send.assert_any_call("Scan.FrameGet")


def test_station_integration(instrument):
    station = Station()
    station.add_component(instrument)
    assert station.components["nanonis"] is instrument
