"""Regression: Scan.Action direction encoding (PDF p.98: 1=up, 0=down).

The command-layer scan path must be independent of qcodes, so this guards the
qcodes-free ``ScanProxy``. Before the fix both ``ScanProxy.start`` and
``ScanChannel.start`` sent ``up=0, down=1`` -- the inverse of the protocol -- so
``start("up")`` physically scanned *down*.
"""

import pytest

from nanonis.command.proxies import ScanProxy


class RecordingController:
    """Minimal stand-in for a controller: records ``send`` calls verbatim."""

    def __init__(self):
        self.calls = []

    def send(self, command, *args):
        self.calls.append((command, args))
        return None


@pytest.mark.parametrize(
    "direction, expected_dir",
    [("up", 1), ("down", 0)],
)
def test_scan_proxy_start_direction_encoding(direction, expected_dir):
    ctrl = RecordingController()
    ScanProxy(ctrl).start(direction)
    assert ctrl.calls == [("Scan.Action", (0, expected_dir))]


def test_scan_proxy_start_defaults_to_up():
    ctrl = RecordingController()
    ScanProxy(ctrl).start()
    assert ctrl.calls == [("Scan.Action", (0, 1))]
