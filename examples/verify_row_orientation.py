"""Characterize ``FrameDataGrab`` row orientation on a real Nanonis controller.

The one scan unknown left after ``verify_waitendofline.py``: when
``FrameDataGrab`` returns the frame matrix, is matrix **row 0** the frame's
**local top** edge (high local-Y, before rotation) or the **local bottom** edge
-- and does an *up* vs *down* scan change that? This is a **data-layout**
property (how the buffer/file orders rows relative to the frame's own geometry),
NOT a statement about absolute space: ``scan/geometry.py`` applies ``row_order``
in frame-local coordinates and *then* rotates by ``frame.angle``, so the answer
is **angle-invariant** and is composed with the angle downstream. Its required
``row_order`` argument is ``"top_to_bottom"`` (row 0 = local top edge) or
``"bottom_to_top"`` (row 0 = local bottom edge); the deferred QCoDeS scan
adapter is gated on it.

Characterize at ``angle == 0`` so that "up starts at the local bottom edge" is
unambiguous and the frame-local edges coincide with screen top/bottom. The
``row_order`` you obtain is then valid at every angle.

The method is **sample-independent** -- no recognizable surface feature needed.
A partial scan (``run_partial(max_lines=N)`` with ``N`` well below the frame's
line count) fills only the first ``N`` *scanned* rows and leaves the rest NaN.
Which matrix end the finite block lands on tells you where the scan-start edge
sits in the matrix. Running it in **both directions** separates two buffer
models that need different handling:

- **physically-indexed** -- matrix row 0 is a fixed physical edge; *up* and
  *down* fill **opposite** matrix ends. ``row_order`` is a single constant.
- **acquisition-ordered** -- matrix row 0 is always the first-*scanned* row;
  *up* and *down* fill the **same** matrix end. ``row_order`` then depends on
  the scan direction, and ``scan_coordinate_grids`` must be told which.

This is corroborated by ``Scan.WaitEndOfLine`` (via ``run_partial``, which stops
after exactly ``N`` scanned image rows); the *orientation* answer comes from
where the finite rows land in the grabbed matrix, which ``WaitEndOfLine`` alone
cannot reveal.

SAFETY: this STARTS A SCAN and MOVES THE TIP, TWICE (up then down). Read
``scan_workflow_live_demo.ipynb`` first and replace every placeholder below with
rig-approved values. It runs only when you pass the confirmation token, e.g.::

    python verify_row_orientation.py VERIFY_ROW_ORIENTATION

Offline, without hardware, you can exercise the pure analysis on synthetic
buffers::

    python verify_row_orientation.py SELFTEST

All distances/speeds are SI (metres, seconds, m/s).
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

EXAMPLES_DIR = Path(__file__).resolve().parent
ROOT = EXAMPLES_DIR
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
if not (ROOT / "src" / "nanonis").exists():  # pragma: no cover - import guard
    raise RuntimeError("Run from the repository root or examples directory")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(EXAMPLES_DIR))  # so `rig_safety_policies` is importable

from nanonis.command import NanonisController  # noqa: E402
from nanonis.workflows import NaNPolicy, ScanSafetyPolicy  # noqa: E402
from nanonis.workflows.scan import ScanConfig, ScanRegion, ScanResult, scan  # noqa: E402

logger = logging.getLogger("verify_row_orientation")

# --- Rig configuration: replace every value below with approved settings. ---
HOST = "127.0.0.1"
PORT = 6504
CONFIRMATION_TOKEN = "VERIFY_ROW_ORIENTATION"
# The safety policy is pulled from the versioned, lab-approval-gated rig registry
# rather than hardcoded here, so this script cannot start a scan against
# unapproved piezo limits. Set RIG_ID to your rig's entry in rig_safety_policies.
RIG_ID = "demo-6504"

# Request clearly fewer rows than the frame has so the finite block is an
# unambiguous, contiguous slice well away from a full frame.
FRAME_LINES = 16
MAX_LINES = 6

# Nanonis scan-direction convention: which physical frame edge does an "up"
# scan START from? The GUI convention is that "up" rasters bottom -> top, so it
# starts at the BOTTOM edge. This is the ONE assumption that maps the observed
# matrix end onto a physical edge; if your controller/GUI shows otherwise, flip
# it and the verdict re-maps. The raw per-direction observations are printed
# regardless, so a wrong assumption here can be reinterpreted after the fact.
UP_STARTS_AT = "bottom"  # "bottom" or "top"


@dataclass(frozen=True)
class DirectionObservation:
    """Where the finite (scanned) rows landed in one direction's grabbed matrix."""

    direction: str            # "up" or "down"
    lines: int                # total rows in the frame matrix
    finite_rows: tuple[int, ...]  # matrix row indices that hold finite data
    location: str             # "front" | "back" | "full" | "none" | "scattered"
    contiguous: bool


def build_safety_policy() -> ScanSafetyPolicy:
    """Return the lab-approved policy for ``RIG_ID``.

    Delegates to ``rig_safety_policies.require_approved``, which raises until a
    qualified operator has reviewed the rig's limits and set ``approved=True``.
    This is the gate that keeps the characterization scan off unapproved piezo
    limits; approve the rig entry before running live.
    """
    from rig_safety_policies import require_approved

    return require_approved(RIG_ID)


def build_region() -> ScanRegion:
    """The frame to scan. ``angle=0`` so frame-local edges == screen top/bottom."""
    return ScanRegion(center_x=0.0, center_y=0.0, width=10e-9, height=10e-9, angle=0.0)


def build_config(
    direction: Literal["up", "down"], channel_index: int = 0
) -> ScanConfig:
    """A small, conservative scan. Confirm ``channel_index`` against Signals.NamesGet."""
    return ScanConfig(
        channel_indexes=(channel_index,),
        direction=direction,
        pixels=16,
        lines=FRAME_LINES,
        forward_line_time=0.05,
        backward_line_time=0.05,
        autosave="off",
        series_name="row-orientation-verify",
        comment="FrameDataGrab row-orientation characterization",
        data_directions=("forward",),
        grab_data=True,
        restore_state=True,
        restore_tip_state=False,
    )


def classify_finite_block(data: np.ndarray, direction: str) -> DirectionObservation:
    """Pure analysis: locate the block of finite (scanned) rows in one matrix.

    A row counts as scanned if it holds any finite value. On a clean partial
    scan the finite rows form a contiguous slice touching one matrix edge:
    ``front`` (includes row 0) or ``back`` (includes the last row). Anything
    else -- the whole frame finite, nothing finite, or a non-contiguous set --
    is reported as ``full`` / ``none`` / ``scattered`` and is inconclusive
    (unscanned rows may be holding stale buffer data rather than NaN).
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim != 2:
        raise ValueError("scan image data must be two-dimensional")
    lines = arr.shape[0]
    finite_mask = np.isfinite(arr).any(axis=1)
    finite = tuple(int(i) for i in np.nonzero(finite_mask)[0])

    n = len(finite)
    if n == 0:
        location, contiguous = "none", False
    elif n == lines:
        location, contiguous = "full", True
    else:
        contiguous = finite == tuple(range(finite[0], finite[-1] + 1))
        if not contiguous:
            location = "scattered"
        elif finite[0] == 0:
            location = "front"       # low matrix indices, includes row 0
        elif finite[-1] == lines - 1:
            location = "back"        # high matrix indices, includes last row
        else:
            location = "scattered"   # contiguous but floating in the middle

    return DirectionObservation(
        direction=direction,
        lines=lines,
        finite_rows=finite,
        location=location,
        contiguous=contiguous,
    )


def _row_order_for_row0_edge(edge: str) -> str:
    """Map 'which physical edge is matrix row 0' onto a geometry ``row_order``."""
    return "bottom_to_top" if edge == "bottom" else "top_to_bottom"


def interpret(
    up_obs: DirectionObservation,
    down_obs: DirectionObservation,
    *,
    up_starts_at: str = UP_STARTS_AT,
) -> dict:
    """Pure analysis: combine the two directions into a ``row_order`` verdict."""
    down_starts_at = "top" if up_starts_at == "bottom" else "bottom"
    clean = {"front", "back"}
    ul, dl = up_obs.location, down_obs.location

    result: dict = {
        "up_location": ul,
        "down_location": dl,
        "up_starts_at": up_starts_at,
        "down_starts_at": down_starts_at,
        "notes": [],
    }

    if ul not in clean or dl not in clean:
        result["buffer_model"] = "inconclusive"
        result["row_order"] = None
        result["up_row_order"] = None
        result["down_row_order"] = None
        result["notes"].append(
            "At least one direction did not yield a clean edge-touching finite "
            f"block (up={ul!r}, down={dl!r}). Likely causes: unscanned rows hold "
            "stale buffer data instead of NaN, MAX_LINES too close to FRAME_LINES, "
            "or a scan didn't stop where expected. Increase FRAME_LINES, lower "
            "MAX_LINES, and re-run; cross-check the WaitEndOfLine row count."
        )
        return result

    if ul != dl:
        # Opposite matrix ends -> matrix row index is a fixed physical position.
        row0_edge = up_starts_at if ul == "front" else down_starts_at
        row_order = _row_order_for_row0_edge(row0_edge)
        result["buffer_model"] = "physically_indexed"
        result["row_order"] = row_order
        result["up_row_order"] = row_order
        result["down_row_order"] = row_order
        result["notes"].append(
            "Up and down filled OPPOSITE matrix ends -> the buffer is physically "
            f"indexed: matrix row 0 is the {row0_edge} edge for both directions. "
            f"Use row_order='{row_order}' in scan_coordinate_grids."
        )
        return result

    # Same matrix end -> matrix row 0 is always the first-scanned row (or the
    # last, if the block sits at the back). row_order then depends on direction.
    first_scanned_at_row0 = ul == "front"
    if first_scanned_at_row0:
        up_edge, down_edge = up_starts_at, down_starts_at
    else:
        up_edge = "top" if up_starts_at == "bottom" else "bottom"
        down_edge = "top" if down_starts_at == "bottom" else "bottom"
    up_row_order = _row_order_for_row0_edge(up_edge)
    down_row_order = _row_order_for_row0_edge(down_edge)
    result["buffer_model"] = "acquisition_ordered"
    result["row_order"] = None  # not a single constant
    result["up_row_order"] = up_row_order
    result["down_row_order"] = down_row_order
    result["notes"].append(
        "Up and down filled the SAME matrix end -> the buffer is acquisition "
        "ordered: matrix row 0 tracks scan progress, not a fixed edge. row_order "
        f"is direction-dependent: up -> '{up_row_order}', down -> "
        f"'{down_row_order}'. scan_coordinate_grids must be given the row_order "
        "that matches the direction actually scanned."
    )
    return result


def run_one_direction(
    nanonis: NanonisController,
    direction: Literal["up", "down"],
    *,
    safety_policy: ScanSafetyPolicy,
    max_lines: int,
) -> ScanResult:
    """Run one partial scan in ``direction`` and return the grabbed result."""
    config = build_config(direction)
    region = build_region()
    workflow = scan(nanonis, safety_policy=safety_policy, nan_policy=NaNPolicy.WARN)
    print(f"Starting {direction!r} partial scan: max_lines={max_lines}, "
          f"frame_lines={config.lines}...", flush=True)
    result = workflow.run_partial(config, region, max_lines=max_lines)
    status_after = nanonis.send("Scan.StatusGet")
    print(f"  scan status after {direction!r} (expect 0/idle):", status_after)
    return result


def _observe(result: ScanResult, direction: str) -> DirectionObservation:
    if not result.images:
        raise RuntimeError(f"{direction!r} scan returned no images")
    return classify_finite_block(result.images[0].data, direction)


def print_report(
    up_obs: DirectionObservation,
    down_obs: DirectionObservation,
    verdict: dict,
) -> None:
    print("\n--- Finite-row observations (per direction) ---")
    for obs in (up_obs, down_obs):
        print(f"  {obs.direction:>4}: lines={obs.lines} location={obs.location} "
              f"contiguous={obs.contiguous} finite_rows={obs.finite_rows}")

    print("\n--- Analysis ---")
    print(f"assumed start edges     : up={verdict['up_starts_at']}, "
          f"down={verdict['down_starts_at']}")
    print(f"up matrix end filled    : {verdict['up_location']}")
    print(f"down matrix end filled  : {verdict['down_location']}")
    print(f"buffer model            : {verdict['buffer_model']}")
    print(f"row_order (fixed)       : {verdict['row_order']}")
    print(f"row_order up / down     : {verdict['up_row_order']} / "
          f"{verdict['down_row_order']}")

    print("\n--- Verdict ---")
    for note in verdict["notes"] or ["No notes."]:
        print(f"  - {note}")
    print(
        "\nReminder: this pins the in-memory FrameDataGrab orientation used by "
        "ScanResult and the QCoDeS adapter. A saved .sxm file may carry its own "
        "header-driven orientation; verify the future data/readers/sxm.py "
        "independently rather than assuming it matches."
    )


def verify(
    nanonis: NanonisController,
    *,
    safety_policy: ScanSafetyPolicy | None = None,
    max_lines: int = MAX_LINES,
    up_starts_at: str = UP_STARTS_AT,
) -> dict:
    """Run up + down partial scans, classify each, and print the verdict."""
    safety_policy = safety_policy or build_safety_policy()

    up_result = run_one_direction(
        nanonis, "up", safety_policy=safety_policy, max_lines=max_lines
    )
    down_result = run_one_direction(
        nanonis, "down", safety_policy=safety_policy, max_lines=max_lines
    )

    up_obs = _observe(up_result, "up")
    down_obs = _observe(down_result, "down")
    verdict = interpret(up_obs, down_obs, up_starts_at=up_starts_at)
    print_report(up_obs, down_obs, verdict)
    return verdict


def selftest() -> int:
    """Exercise the pure analysis on synthetic buffers -- no hardware."""
    lines, n = FRAME_LINES, MAX_LINES

    def partial(front: bool) -> np.ndarray:
        arr = np.full((lines, 4), np.nan)
        rows = range(n) if front else range(lines - n, lines)
        for r in rows:
            arr[r, :] = float(r)
        return arr

    scenarios = {
        "physically_indexed (up->front, down->back)": (partial(True), partial(False)),
        "physically_indexed (up->back, down->front)": (partial(False), partial(True)),
        "acquisition_ordered (both front)": (partial(True), partial(True)),
        "acquisition_ordered (both back)": (partial(False), partial(False)),
        "inconclusive (up full)": (np.zeros((lines, 4)), partial(True)),
    }
    for name, (up_data, down_data) in scenarios.items():
        up_obs = classify_finite_block(up_data, "up")
        down_obs = classify_finite_block(down_data, "down")
        verdict = interpret(up_obs, down_obs)
        print(f"\n### {name}")
        print(f"  up={up_obs.location} down={down_obs.location} -> "
              f"model={verdict['buffer_model']} "
              f"row_order={verdict['row_order']} "
              f"(up={verdict['up_row_order']}, down={verdict['down_row_order']})")
    return 0


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if "SELFTEST" in argv[1:]:
        return selftest()
    if CONFIRMATION_TOKEN not in argv[1:]:
        print(
            "Refusing to start: this moves the tip and runs two scans.\n"
            "Re-run with the confirmation token:\n\n"
            f"    python {Path(__file__).name} {CONFIRMATION_TOKEN}\n\n"
            "Or exercise the offline analysis with:\n\n"
            f"    python {Path(__file__).name} SELFTEST\n"
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
