"""Versioned, per-rig ``ScanSafetyPolicy`` definitions.

!!! DRAFT -- NOT LAB-APPROVED !!!
The numbers below are a starting point derived from a live read-only
characterization (examples/characterize_m4a.py), NOT approved scan limits. A
qualified operator must review and sign off each value before use, then bump
``VERSION`` and record the approval date. The software validates these limits but
cannot choose them.

Usage:
    from examples.rig_safety_policies import RIG_POLICIES
    policy = RIG_POLICIES["demo-6504"].policy
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from nanonis.workflows import ScanSafetyPolicy  # noqa: E402


@dataclass(frozen=True)
class RigPolicy:
    rig_id: str
    version: str
    approved: bool          # flip to True only after lab sign-off
    approved_on: str | None  # ISO date of approval, or None
    measured_piezo_range_m: tuple[float, float, float]  # (X, Y, Z), as characterized
    notes: str
    policy: ScanSafetyPolicy


# --- Rig: the controller reached on 127.0.0.1:6504 during M4-A characterization.
# Measured Piezo.RangeGet: X = Y = 3.000e-6 m, Z = 1.500e-6 m (half-range 1.5 um).
DEMO_6504 = RigPolicy(
    rig_id="demo-6504",
    version="0.1.0-draft",
    approved=False,
    approved_on=None,
    measured_piezo_range_m=(3.000000106e-6, 3.000000106e-6, 1.500000053e-6),
    notes=(
        "Starting point from read-only characterization. piezo_safety_margin of "
        "100 nm trims usable X/Y travel to about +/-1.4 um. Confirm line-time and "
        "linear-speed bounds against the slowest and fastest scans this rig should "
        "ever run. max_pixels/max_lines cap raster size, not physical extent."
    ),
    policy=ScanSafetyPolicy(
        max_pixels=1024,           # raster cap; review for this rig
        max_lines=1024,            # raster cap; review for this rig
        piezo_safety_margin=100e-9,  # m; keeps frames clear of the +/-1.5 um edges
        min_line_time=1e-3,        # s/line; reject implausibly fast lines
        max_line_time=10.0,        # s/line; reject implausibly slow lines
        min_linear_speed=1e-12,    # m/s
        max_linear_speed=1e-2,     # m/s
        tip=None,                  # add a TipRestorePolicy only after approval
    ),
)


RIG_POLICIES: dict[str, RigPolicy] = {
    DEMO_6504.rig_id: DEMO_6504,
}


def require_approved(rig_id: str) -> ScanSafetyPolicy:
    """Return a policy only if it has been marked lab-approved."""
    entry = RIG_POLICIES[rig_id]
    if not entry.approved:
        raise RuntimeError(
            f"Rig '{rig_id}' policy {entry.version} is a draft and not lab-approved; "
            "review the values and set approved=True (with approved_on) first."
        )
    return entry.policy


if __name__ == "__main__":
    for rig_id, entry in RIG_POLICIES.items():
        status = "APPROVED" if entry.approved else "DRAFT (not approved)"
        print(f"[{status}] {rig_id} v{entry.version}")
        print("  measured piezo range (m):", entry.measured_piezo_range_m)
        print("  policy:", entry.policy)
