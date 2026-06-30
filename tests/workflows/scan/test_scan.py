from dataclasses import replace

import numpy as np
import pytest

from nanonis.workflows import (
    SafetyPreflightError,
    ScanResponseError,
    ScanSafetyPolicy,
    ScanTimeoutError,
    ScanWorkflow,
    StateRestorationError,
    WorkflowError,
)
from nanonis.workflows.scan import ScanConfig, estimate_scan_duration

from ..conftest import RecoverableFakeController
from .test_models import buffer, frame, props, speed


def policy():
    return ScanSafetyPolicy(
        max_pixels=1024,
        max_lines=1024,
        piezo_safety_margin=1e-9,
        min_line_time=1e-4,
        max_line_time=10,
        min_linear_speed=1e-12,
        max_linear_speed=1,
    )


def config(**changes):
    return replace(ScanConfig((0,)), **changes)


def frame_data(direction=1):
    return {
        "channel_name": "Current (A)",
        "scan_data_rows": 3,
        "scan_data_columns": 4,
        "scan_data": np.arange(12).reshape(3, 4),
        "scan_direction": direction,
    }


def scripted_controller(*, wait=None):
    client = RecoverableFakeController()
    client.script("Piezo.RangeGet", {"range_x_m": 1e-6, "range_y_m": 1e-6,
                                     "range_z_m": 1e-6})
    client.script("Signals.NamesGet", {"signals_names": ["I", "Z"]})
    # preflight, transaction snapshot, effective readback
    client.script("Scan.FrameGet", frame(), frame(), frame())
    client.script("Scan.BufferGet", buffer(), buffer(), buffer())
    client.script("Scan.PropsGet", props(), props(), props(continuous=0))
    client.script("Scan.SpeedGet", speed(), speed(), speed())
    client.script("Scan.StatusGet", 0)
    client.script(
        "Scan.WaitEndOfScan",
        {"timeout_status": 0, "file_path": "C:/data/scan.sxm"}
        if wait is None else wait,
    )
    client.script("Scan.FrameDataGrab", frame_data())
    return client


def test_invalid_request_sends_nothing():
    client = RecoverableFakeController()
    with pytest.raises(SafetyPreflightError):
        ScanWorkflow(client, safety_policy=policy()).run(config(pixels=2048))
    assert client.sent == []


def test_configuration_failure_message_includes_underlying_error():
    client = scripted_controller()
    client.fail("Scan.FrameSet", RuntimeError("controller rejected frame"))

    with pytest.raises(
        WorkflowError, match="frame: controller rejected frame"
    ):
        ScanWorkflow(client, safety_policy=policy()).run(config())


@pytest.mark.parametrize("unsafe_skip_preflight", [False, True])
def test_too_small_explicit_timeout_is_rejected_before_setters(
    unsafe_skip_preflight,
):
    client = scripted_controller()

    with pytest.raises(
        SafetyPreflightError, match="must exceed the Nanonis controller-side timeout"
    ):
        ScanWorkflow(client, safety_policy=policy()).run(
            config(acquisition_timeout=1),
            unsafe_skip_preflight=unsafe_skip_preflight,
        )

    assert not any(command.endswith("Set") for command, _, _ in client.sent)


def test_malformed_status_mapping_raises_scan_response_error():
    client = scripted_controller()
    client._responses["Scan.StatusGet"].clear()
    client.script("Scan.StatusGet", {})

    with pytest.raises(ScanResponseError, match="missing 'scan_status'"):
        ScanWorkflow(client, safety_policy=policy()).run(config())

    assert not any(command == "Scan.Action" for command, _, _ in client.sent)


def test_end_to_end_snapshot_apply_start_grab_and_restore():
    client = scripted_controller()
    result = ScanWorkflow(client, safety_policy=policy()).run(config())

    commands = [entry[0] for entry in client.sent]
    start = commands.index("Scan.Action")
    assert client.sent[start][1] == (0, 1)  # start, up
    wait_call = next(entry for entry in client.sent if entry[0] == "Scan.WaitEndOfScan")
    assert wait_call[2] > wait_call[1][0] / 1000
    assert result.saved_path == "C:/data/scan.sxm"
    assert result.images[0].data.shape == (3, 4)
    assert result.acquisition_timeout_used == wait_call[2]
    prop_calls = [entry for entry in client.sent if entry[0] == "Scan.PropsSet"]
    assert prop_calls[0][1][0] == 2  # desired continuous off
    assert prop_calls[-1][1][0] == 1  # original continuous on restored


@pytest.mark.parametrize(("direction", "wire"), [("up", 1), ("down", 0)])
def test_direction_constants(direction, wire):
    client = scripted_controller()
    ScanWorkflow(client, safety_policy=policy()).run(config(direction=direction))
    start = next(entry for entry in client.sent if entry[0] == "Scan.Action")
    assert start[1] == (0, wire)


def test_controller_timeout_recovers_stop_then_restores():
    client = scripted_controller(wait={"timeout_status": 1, "file_path": ""})
    client.script("Scan.StatusGet", 1, 0)

    with pytest.raises(ScanTimeoutError):
        ScanWorkflow(client, safety_policy=policy()).run(config())

    commands = [entry[0] for entry in client.sent]
    wait = commands.index("Scan.WaitEndOfScan")
    stop = next(
        index for index, entry in enumerate(client.sent)
        if index > wait and entry[0] == "Scan.Action" and entry[1][0] == 1
    )
    restored = commands.index("Scan.FrameSet", stop)
    assert client.reconnect_count == 1
    assert stop < restored


def test_any_post_start_error_recovers():
    client = scripted_controller()
    client._responses["Scan.WaitEndOfScan"].clear()
    client.fail("Scan.WaitEndOfScan", RuntimeError("Nanonis error"))
    client.script("Scan.StatusGet", 1, 0)

    with pytest.raises(RuntimeError, match="Nanonis error"):
        ScanWorkflow(client, safety_policy=policy()).run(config())

    assert client.reconnect_count == 1
    assert any(entry[0] == "Scan.Action" and entry[1][0] == 1 for entry in client.sent)


def test_grabs_every_channel_and_saved_direction():
    client = scripted_controller()
    client._responses["Signals.NamesGet"].clear()
    client.script("Signals.NamesGet", {"signals_names": ["I", "Z"]})
    for queue in (client._responses["Scan.BufferGet"],):
        queue.clear()
    two = {"num_channels": 2, "channel_indexes": [0, 1], "pixels": 4, "lines": 3}
    client.script("Scan.BufferGet", two, two, two)
    client._responses["Scan.FrameDataGrab"].clear()
    client.script("Scan.FrameDataGrab", frame_data(), frame_data(), frame_data(), frame_data())

    result = ScanWorkflow(client, safety_policy=policy()).run(
        config(channel_indexes=(0, 1), data_directions=("forward", "backward"))
    )

    calls = [entry[1] for entry in client.sent if entry[0] == "Scan.FrameDataGrab"]
    assert calls == [(0, 1), (0, 0), (1, 1), (1, 0)]
    assert len(result.images) == 4


def test_completed_result_survives_restoration_failure():
    client = scripted_controller()
    client.script("Scan.FrameSet", None, lambda *_: (_ for _ in ()).throw(RuntimeError("restore")))

    with pytest.raises(StateRestorationError) as caught:
        ScanWorkflow(client, safety_policy=policy()).run(config())

    assert caught.value.result is not None
    assert caught.value.result.saved_path.endswith("scan.sxm")


def test_duration_uses_both_raster_passes_not_saved_directions():
    client = scripted_controller()
    from nanonis.workflows.scan import ScanSettings

    # Consume one typed settings snapshot directly.
    settings = ScanSettings.snapshot(client)
    assert estimate_scan_duration(settings) == pytest.approx(1 + 3 * (0.01 + 0.02))


def test_rotated_frame_outside_piezo_range_fails_closed():
    client = scripted_controller()
    with pytest.raises(SafetyPreflightError, match="piezo range"):
        ScanWorkflow(client, safety_policy=policy()).run(
            config(center_x=0.49e-6, width=0.1e-6, angle=45)
        )
    assert not any(entry[0] == "Scan.Action" for entry in client.sent)


# WaitEndOfLine returns, modelled on the live controller characterization in
# examples/verify_waitendofline.py: a short startup transient, then one trace
# (movement 0) plus one retrace (movement 1) return per image row, with 1-based
# line numbers. run_partial counts a row at each trace return (line_number >= 1).
def trace(line_number, pass_number=1):
    return {"timeout_status": 0, "line_number": line_number,
            "type_of_movement": 0, "pass_number": pass_number}


def retrace(line_number, pass_number=1):
    return {"timeout_status": 0, "line_number": line_number,
            "type_of_movement": 1, "pass_number": pass_number}


def startup_sentinel():
    # Observed leading return that does not correspond to a data row.
    return {"timeout_status": 0, "line_number": -1,
            "type_of_movement": 3, "pass_number": 0}


def wol_rows(rows, *, sentinel=True):
    seq = [startup_sentinel()] if sentinel else []
    for line_number in range(1, rows + 1):
        seq.append(trace(line_number))
        seq.append(retrace(line_number))
    return seq


def traces_seen(seen):
    return [s for s in seen if s[1] == 0 and s[0] >= 1]


def scripted_partial_controller(*, returns, status_stream=None):
    """Like ``scripted_controller`` but scripted for ``run_partial``.

    The frame has 3 lines (see ``buffer()``). ``returns`` is the queued
    ``Scan.WaitEndOfLine`` stream; ``status_stream`` is what ``Scan.StatusGet``
    reports after the preflight idle reading (default: enough "running" values).
    """
    client = RecoverableFakeController()
    client.script("Piezo.RangeGet", {"range_x_m": 1e-6, "range_y_m": 1e-6,
                                     "range_z_m": 1e-6})
    client.script("Signals.NamesGet", {"signals_names": ["I", "Z"]})
    client.script("Scan.FrameGet", frame(), frame(), frame())
    client.script("Scan.BufferGet", buffer(), buffer(), buffer())
    client.script("Scan.PropsGet", props(), props(), props(continuous=0))
    client.script("Scan.SpeedGet", speed(), speed(), speed())
    if status_stream is None:
        status_stream = [1] * (len(returns) + 4)
    # preflight idle (0), then the running/idle stream consulted per return.
    client.script("Scan.StatusGet", 0, *status_stream)
    client.script("Scan.WaitEndOfLine", *returns)
    client.script("Scan.FrameDataGrab", frame_data())
    return client


def test_partial_scan_stops_after_max_rows():
    client = scripted_partial_controller(returns=wol_rows(3))
    seen = []
    result = ScanWorkflow(client, safety_policy=policy()).run_partial(
        config(), max_lines=2,
        on_line=lambda ln, mv, ps: seen.append((ln, mv, ps)),
    )

    # Two image rows (trace returns) counted before stopping early.
    assert len(traces_seen(seen)) == 2
    # Consumed sentinel, trace1, retrace1, trace2 -> stops at the 2nd trace.
    wol = [e for e in client.sent if e[0] == "Scan.WaitEndOfLine"]
    assert len(wol) == 4
    # Per-line socket timeout must exceed the controller-side line timeout.
    assert wol[0][2] > wol[0][1][0] / 1000
    start = next(e for e in client.sent if e[0] == "Scan.Action" and e[1][0] == 0)
    stop = next(e for e in client.sent if e[0] == "Scan.Action" and e[1][0] == 1)
    assert start[1] == (0, 1)  # start, up
    assert client.sent.index(start) < client.sent.index(stop)
    assert result.saved_path == ""  # partial scans are not auto-saved
    assert not any(e[0] == "Scan.WaitEndOfScan" for e in client.sent)


def test_partial_scan_caps_max_rows_at_frame_lines():
    client = scripted_partial_controller(returns=wol_rows(3))  # frame has 3 lines
    seen = []
    ScanWorkflow(client, safety_policy=policy()).run_partial(
        config(), max_lines=99,
        on_line=lambda ln, mv, ps: seen.append((ln, mv, ps)),
    )
    assert len(traces_seen(seen)) == 3


def test_partial_scan_on_line_callback_can_abort():
    client = scripted_partial_controller(returns=wol_rows(3))
    seen = []

    def on_line(line_number, movement, pass_number):
        seen.append((line_number, movement, pass_number))
        return False if movement == 0 and line_number >= 1 else None

    ScanWorkflow(client, safety_policy=policy()).run_partial(
        config(), max_lines=3, on_line=on_line
    )

    # Sentinel observed, then aborted at the first trace.
    assert seen == [(-1, 3, 0), (1, 0, 1)]
    assert sum(e[0] == "Scan.WaitEndOfLine" for e in client.sent) == 2
    assert any(e[0] == "Scan.Action" and e[1][0] == 1 for e in client.sent)


def test_partial_scan_stops_when_frame_finishes_early():
    # Status: running after the sentinel, then idle after the first row.
    client = scripted_partial_controller(returns=wol_rows(3), status_stream=[1, 0])
    seen = []
    ScanWorkflow(client, safety_policy=policy()).run_partial(
        config(), max_lines=3,
        on_line=lambda ln, mv, ps: seen.append((ln, mv, ps)),
    )
    assert len(traces_seen(seen)) == 1  # stopped after one row (status idle)
    assert sum(e[0] == "Scan.WaitEndOfLine" for e in client.sent) == 2


def test_partial_scan_warns_when_no_rows_counted(caplog):
    # A controller that only ever emits non-trace movements: no row can be
    # counted, so the loop must give up at its safety bound and warn.
    client = scripted_partial_controller(returns=[startup_sentinel()] * 20)
    with caplog.at_level("WARNING"):
        ScanWorkflow(client, safety_policy=policy()).run_partial(
            config(), max_lines=2
        )
    # max_returns = 2 rows * 2 + 6 startup budget = 10.
    assert sum(e[0] == "Scan.WaitEndOfLine" for e in client.sent) == 10
    assert any("movement encoding" in r.getMessage() for r in caplog.records)
    assert any(e[0] == "Scan.Action" and e[1][0] == 1 for e in client.sent)


def test_partial_scan_line_timeout_recovers():
    client = scripted_partial_controller(returns=wol_rows(2))
    client._responses["Scan.WaitEndOfLine"].clear()
    client.script("Scan.WaitEndOfLine", {"timeout_status": 1, "line_number": -1,
                                         "type_of_movement": 3, "pass_number": 0})
    client._responses["Scan.StatusGet"].clear()
    client.script("Scan.StatusGet", 0, 1, 0)  # preflight, recovery running, stopped

    with pytest.raises(ScanTimeoutError):
        ScanWorkflow(client, safety_policy=policy()).run_partial(
            config(), max_lines=2
        )

    assert client.reconnect_count == 1
    assert any(e[0] == "Scan.Action" and e[1][0] == 1 for e in client.sent)


def test_partial_scan_rejects_nonpositive_max_lines():
    client = scripted_partial_controller(returns=wol_rows(1))
    with pytest.raises(ValueError, match="positive integer"):
        ScanWorkflow(client, safety_policy=policy()).run_partial(
            config(), max_lines=0
        )
    assert client.sent == []
