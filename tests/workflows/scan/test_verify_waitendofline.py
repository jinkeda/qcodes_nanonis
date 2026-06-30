"""Offline tests for the WaitEndOfLine characterization analysis.

The hardware path can't run here; these cover the pure ``summarize_line_records``
verdict logic and the best-effort row counter.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "examples" / "verify_waitendofline.py"
_spec = importlib.util.spec_from_file_location("verify_waitendofline", SCRIPT)
vw = importlib.util.module_from_spec(_spec)
sys.modules["verify_waitendofline"] = vw  # dataclass needs the module registered
_spec.loader.exec_module(vw)


def records(pairs):
    """Build LineRecord list from (line_number, movement) pairs."""
    return [
        vw.LineRecord(index=i, elapsed_s=0.05 * i, line_number=ln,
                      movement=mv, pass_number=1)
        for i, (ln, mv) in enumerate(pairs)
    ]


def test_one_return_per_row_is_recognized():
    recs = records([(1, 0), (2, 0), (3, 0), (4, 0)])  # 1-based, all traces
    report = vw.summarize_line_records(recs, max_lines=4, frame_lines=16, data_rows=4)
    assert report["semantics"] == "one_return_per_row"
    assert report["rows"] == 4
    assert report["status_running_ok"] is True
    assert any("equals the return count" in note for note in report["notes"])


def test_two_returns_per_row_is_flagged():
    # startup sentinel, then trace + retrace pairs with 1-based line numbers.
    recs = records([(-1, 3), (1, 0), (1, 1), (2, 0), (2, 1)])
    report = vw.summarize_line_records(recs, max_lines=2, frame_lines=16, data_rows=2)
    assert report["semantics"] == "multiple_returns_per_row"
    assert report["rows"] == 2  # two trace returns, sentinel ignored
    assert report["status_running_ok"] is True
    assert any("trace return" in note for note in report["notes"])
    assert any("match the trace-counted rows" in note for note in report["notes"])


def test_fewer_rows_than_expected_flags_status():
    recs = records([(-1, 3), (1, 0), (1, 1)])  # asked for 4 rows, got 1 trace
    report = vw.summarize_line_records(recs, max_lines=4, frame_lines=16)
    assert report["rows"] == 1
    assert report["status_running_ok"] is False
    assert any("read idle mid-scan" in note for note in report["notes"])


def test_max_lines_capped_at_frame_lines():
    recs = records([(1, 0), (2, 0), (3, 0)])  # frame only has 3 lines
    report = vw.summarize_line_records(recs, max_lines=99, frame_lines=3)
    assert report["expected_rows"] == 3
    assert report["status_running_ok"] is True


def test_no_returns_is_inconclusive():
    report = vw.summarize_line_records([], max_lines=4, frame_lines=16)
    assert report["semantics"] == "no_returns"


def test_count_data_rows_counts_finite_rows():
    class FakeImage:
        def __init__(self, data):
            self.data = data

    class FakeResult:
        def __init__(self, images):
            self.images = images

    data = np.array([
        [1.0, 2.0, 3.0],
        [np.nan, np.nan, np.nan],
        [4.0, 5.0, 6.0],
    ])
    assert vw.count_data_rows(FakeResult((FakeImage(data),))) == 2
    assert vw.count_data_rows(FakeResult(())) is None  # no images grabbed
