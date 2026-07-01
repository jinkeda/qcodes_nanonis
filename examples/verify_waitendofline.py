"""Characterize ``Scan.WaitEndOfLine`` semantics on a real Nanonis controller.

``ScanWorkflow.run_partial`` assumes two things about the controller that are
documented as "verify on hardware". This script settles both, end to end:

1. **Does one ``WaitEndOfLine`` return correspond to one data row?**
   If a raster line is a trace *and* a retrace, the controller may emit two
   returns per row. ``run_partial`` counts returns, and caps the loop at
   ``min(max_lines, effective.lines)`` -- which is only correct when one return
   equals one row. The line-number / movement sequence reported per return
   answers this directly from the protocol, independent of any NaN assumption.

2. **Does ``Scan.StatusGet`` report 1 (running) for the whole scan?**
   ``run_partial`` breaks early if status reads idle, so if the controller
   briefly reports idle mid-scan it would stop short. Requesting fewer lines
   than the frame has and checking that exactly that many returns arrive
   confirms status stayed "running" throughout.

SAFETY: this STARTS A SCAN and MOVES THE TIP. Read
``scan_workflow_live_demo.ipynb`` first and replace every placeholder below with
rig-approved values. It runs only when you pass the confirmation token, e.g.::

    python verify_waitendofline.py VERIFY_WAITENDOFLINE

All distances/speeds are SI (metres, seconds, m/s).
"""

from __future__ import annotations

import logging
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
if not (ROOT / "src" / "nanonis").exists():  # pragma: no cover - import guard
    raise RuntimeError("Run from the repository root or examples directory")
sys.path.insert(0, str(ROOT / "src"))

from nanonis.command import NanonisController  # noqa: E402
from nanonis.workflows import NaNPolicy, ScanSafetyPolicy  # noqa: E402
from nanonis.workflows.scan import ScanConfig, ScanRegion, ScanResult, scan  # noqa: E402

logger = logging.getLogger("verify_waitendofline")

# --- Rig configuration: replace every value below with approved settings. ---
HOST = "127.0.0.1"
PORT = 6504
CONFIRMATION_TOKEN = "VERIFY_WAITENDOFLINE"

# Request fewer lines than the frame has so an early stop is unambiguous.
FRAME_LINES = 16
MAX_LINES = 12


@dataclass(frozen=True)
class LineRecord:
    """One ``Scan.WaitEndOfLine`` return, as surfaced by the on_line callback."""

    index: int          # 0-based order in which the return arrived
    elapsed_s: float    # seconds since the scan started
    line_number: int    # controller "Line number" field
    movement: int       # controller "Type of movement" field
    pass_number: int    # controller "Pass number" field


def build_safety_policy() -> ScanSafetyPolicy:
    """Replace with values approved for this scanner (see the live notebook)."""
    return ScanSafetyPolicy(
        max_pixels=1024,
        max_lines=1024,
        piezo_safety_margin=10e-9,
        min_line_time=1e-3,
        max_line_time=10.0,
        min_linear_speed=1e-12,
        max_linear_speed=1e-2,
        tip=None,
    )


def build_region() -> ScanRegion:
    """The small frame to scan (SI metres); confirm it is safe for the rig."""
    return ScanRegion(center_x=0.0, center_y=0.0, width=10e-9, height=10e-9)


def build_config(channel_index: int = 0) -> ScanConfig:
    """A small, conservative scan. Confirm ``channel_index`` against Signals.NamesGet."""
    return ScanConfig(
        channel_indexes=(channel_index,),
        direction="up",
        pixels=16,
        lines=FRAME_LINES,
        forward_line_time=0.05,
        backward_line_time=0.05,
        autosave="off",
        series_name="waitendofline-verify",
        comment="WaitEndOfLine semantics characterization",
        data_directions=("forward",),
        grab_data=True,
        restore_state=True,
        restore_tip_state=False,
    )


def record_lines() -> tuple[list[LineRecord], callable]:
    """Build an on_line callback that appends a LineRecord for every return."""
    records: list[LineRecord] = []
    start = time.monotonic()

    def on_line(line_number: int, movement: int, pass_number: int) -> None:
        records.append(
            LineRecord(
                index=len(records),
                elapsed_s=time.monotonic() - start,
                line_number=line_number,
                movement=movement,
                pass_number=pass_number,
            )
        )
        # Returning None lets the scan run to ``max_lines``; this is pure
        # observation, no early abort.

    return records, on_line


def count_data_rows(result: ScanResult) -> int | None:
    """Best-effort count of rows that contain finite data in the first image.

    This is corroborating evidence only: on hardware, unscanned rows may hold
    stale buffer data rather than NaN, so trust the line-number analysis first.
    """
    if not result.images:
        return None
    data = np.asarray(result.images[0].data)
    if data.ndim != 2:
        return None
    return int(np.count_nonzero(np.isfinite(data).any(axis=1)))


def summarize_line_records(
    records: list[LineRecord],
    *,
    max_lines: int,
    frame_lines: int,
    data_rows: int | None = None,
) -> dict:
    """Pure analysis of the recorded returns; no hardware access.

    Returns a report dict with a ``semantics`` verdict, a ``status_running_ok``
    flag, and human-readable ``notes``.
    """
    returns = len(records)
    line_numbers = [r.line_number for r in records]
    movements = [r.movement for r in records]
    counts = Counter(line_numbers)
    max_per_line = max(counts.values()) if counts else 0
    # run_partial counts an image row at each trace return; mirror that here.
    rows = sum(1 for r in records if r.movement == 0 and r.line_number >= 1)
    expected_rows = min(max_lines, frame_lines)

    if returns == 0:
        semantics = "no_returns"
    elif max_per_line == 1 and line_numbers == sorted(line_numbers):
        semantics = "one_return_per_row"
    elif max_per_line >= 2:
        semantics = "multiple_returns_per_row"
    else:
        semantics = "inconclusive"

    # run_partial stops after `expected_rows` trace returns; seeing exactly that
    # many proves StatusGet never read idle mid-scan and no line timed out.
    status_running_ok = rows == expected_rows

    notes: list[str] = []
    if semantics == "multiple_returns_per_row":
        notes.append(
            "Controller emits >1 WaitEndOfLine return per row (trace+retrace). "
            "run_partial counts image rows at each trace return (movement == 0, "
            "line_number >= 1); confirm the trace returns below carry movement == 0 "
            "so its row count is correct on this rig."
        )
    if semantics == "one_return_per_row":
        notes.append(
            "One return == one image row: run_partial's row count equals the "
            "return count here."
        )
    if not status_running_ok:
        notes.append(
            f"Expected {expected_rows} image rows (trace returns) but counted "
            f"{rows}: StatusGet may have read idle mid-scan, a line timed out, or "
            "trace movements are not encoded as 0. Investigate before trusting "
            "run_partial's row count."
        )
    if data_rows is not None and rows:
        if data_rows == rows:
            notes.append(
                f"Finite data rows ({data_rows}) match the trace-counted rows ({rows})."
            )
        else:
            notes.append(
                f"Finite data rows ({data_rows}) != trace-counted rows ({rows}); the "
                "buffer may hold stale rows, so weigh the line-number evidence above."
            )

    return {
        "returns": returns,
        "rows": rows,
        "expected_rows": expected_rows,
        "distinct_line_numbers": sorted(counts),
        "max_returns_per_line": max_per_line,
        "movement_values": sorted(set(movements)),
        "semantics": semantics,
        "status_running_ok": status_running_ok,
        "data_rows": data_rows,
        "notes": notes,
    }


def print_report(records: list[LineRecord], report: dict) -> None:
    print("\n--- Raw WaitEndOfLine returns ---")
    print(f"{'idx':>3} {'elapsed_s':>10} {'line_no':>8} {'movement':>9} {'pass':>5}")
    for r in records:
        print(f"{r.index:>3} {r.elapsed_s:>10.3f} {r.line_number:>8} "
              f"{r.movement:>9} {r.pass_number:>5}")

    print("\n--- Analysis ---")
    print(f"returns                 : {report['returns']}")
    print(f"trace-counted rows      : {report['rows']} (expected {report['expected_rows']})")
    print(f"distinct line numbers   : {report['distinct_line_numbers']}")
    print(f"max returns per line    : {report['max_returns_per_line']}")
    print(f"movement values seen    : {report['movement_values']}")
    print(f"finite data rows        : {report['data_rows']}")
    print(f"WaitEndOfLine semantics : {report['semantics']}")
    print(f"StatusGet stayed running: {report['status_running_ok']}")
    print("\n--- Verdict ---")
    for note in report["notes"] or ["No notes."]:
        print(f"  - {note}")


def verify(
    nanonis: NanonisController,
    *,
    safety_policy: ScanSafetyPolicy | None = None,
    config: ScanConfig | None = None,
    max_lines: int = MAX_LINES,
) -> dict:
    """Run a small partial scan, characterize the returns, and print a report."""
    safety_policy = safety_policy or build_safety_policy()
    config = config or build_config()
    region = build_region()
    records, on_line = record_lines()

    workflow = scan(nanonis, safety_policy=safety_policy, nan_policy=NaNPolicy.WARN)
    print(f"Starting characterization scan: max_lines={max_lines}, "
          f"frame_lines={config.lines}...", flush=True)
    result = workflow.run_partial(config, region, max_lines=max_lines, on_line=on_line)

    # Confirm the module returned to idle after the workflow stopped it.
    status_after = nanonis.send("Scan.StatusGet")
    print("Scan status after workflow (expect 0/idle):", status_after)

    report = summarize_line_records(
        records,
        max_lines=max_lines,
        frame_lines=config.lines,
        data_rows=count_data_rows(result),
    )
    report["status_idle_after"] = status_after == 0
    print_report(records, report)
    return report


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if CONFIRMATION_TOKEN not in argv[1:]:
        print(
            "Refusing to start: this moves the tip and runs a scan.\n"
            f"Re-run with the confirmation token:\n\n"
            f"    python {Path(__file__).name} {CONFIRMATION_TOKEN}\n"
        )
        return 1

    nanonis = NanonisController(
        host=HOST,
        port=PORT,
        config_path=ROOT / "configs" / "commands",
        timeout=10.0,
    )
    nanonis.connect()
    print("Connected:", nanonis.is_connected)
    try:
        verify(nanonis)
    finally:
        nanonis.disconnect()
        print("Disconnected:", not nanonis.is_connected)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main(sys.argv))
