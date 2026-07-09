"""Read-only live acceptance run for the polling time-trace workflow.

Set the two signal indexes for the rig. The script records 60 seconds at 10 Hz,
supports graceful first-Ctrl-C cancellation, verifies timing, cross-checks Z
outside the timed loop, and compares before/after read-only state snapshots.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
if not (ROOT / "src" / "nanonis").exists():  # pragma: no cover - import guard
    raise RuntimeError("Run from the repository root or examples directory")
sys.path.insert(0, str(ROOT / "src"))

from nanonis.command import NanonisController  # noqa: E402
from nanonis.workflows import (  # noqa: E402
    CancelToken,
    ProgressEvent,
    TimeTraceConfig,
    TimeTraceWorkflow,
    cancel_on_sigint,
)

HOST = "127.0.0.1"
PORT = 6504
Z_SIGNAL_INDEX = 0  # Replace from Signals.NamesGet.
CURRENT_SIGNAL_INDEX = 1  # Replace from Signals.NamesGet.


def snapshot(nanonis) -> dict[str, Any]:
    return {
        "bias": nanonis.send("Bias.Get"),
        "setpoint": nanonis.send("ZCtrl.SetpntGet"),
        "feedback": nanonis.send("ZCtrl.OnOffGet"),
        "rt_frequency": nanonis.send("Util.RTFreqGet"),
        "acquisition_period": nanonis.send("Util.AcqPeriodGet"),
        "rt_oversampling": nanonis.send("Util.RTOversamplGet"),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def cross_check_z(nanonis) -> list[dict[str, float]]:
    rows = []
    for _ in range(10):
        response = nanonis.send("Signals.ValsGet", 1, (Z_SIGNAL_INDEX,), 1)
        rows.append(
            {
                "Signals.ValsGet": float(response["signals_values"][0]),
                "ZCtrl.ZPosGet": float(nanonis.send("ZCtrl.ZPosGet")),
            }
        )
    return rows


def run_acceptance(nanonis) -> dict[str, Any]:
    before = snapshot(nanonis)
    checks_before = cross_check_z(nanonis)
    token = CancelToken()

    def progress(event: ProgressEvent) -> None:
        print(f"\r{event.message}: {event.elapsed_s:.1f} s", end="", flush=True)

    config = TimeTraceConfig(
        signal_indexes=(Z_SIGNAL_INDEX, CURRENT_SIGNAL_INDEX),
        duration_s=60.0,
        sample_interval_s=0.1,
        wait_for_newest_data=True,
        resolve_names=True,
    )
    print("Starting 60 s trace; first Ctrl-C returns a partial result.")
    with cancel_on_sigint(token):
        result = TimeTraceWorkflow(nanonis).run(
            config, cancel=token, on_progress=progress
        )
    print()

    checks_after = cross_check_z(nanonis)
    after = snapshot(nanonis)
    differences = np.diff(result.elapsed_s)
    p95_error = (
        float(np.percentile(np.abs(differences - config.sample_interval_s), 95))
        if differences.size
        else None
    )
    completed = not result.cancelled
    timing_pass = bool(
        completed
        and result.n_samples == 601
        and result.late_sample_count <= 6
        and 60.0 <= result.elapsed_s[-1] <= 60.6
        and p95_error is not None
        and p95_error <= 0.02
    )
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "metadata": result.to_metadata(),
        "elapsed_s": result.elapsed_s.tolist(),
        "values": result.values.tolist(),
        "p95_interval_error_s": p95_error,
        "timing_gate_passed": timing_pass,
        "state_before": _jsonable(before),
        "state_after": _jsonable(after),
        "state_unchanged": _jsonable(before) == _jsonable(after),
        "z_cross_checks_before": checks_before,
        "z_cross_checks_after": checks_after,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ROOT / "reports" / f"live_time_trace_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Saved:", path)
    print("Timing gate passed:", timing_pass)
    print("State unchanged:", report["state_unchanged"])
    print("Cancelled:", result.cancelled, "samples:", result.n_samples)
    return report


def main() -> int:
    nanonis = NanonisController(
        host=HOST,
        port=PORT,
        config_path=ROOT / "configs" / "commands",
        timeout=10.0,
    )
    nanonis.connect()
    try:
        run_acceptance(nanonis)
    finally:
        nanonis.disconnect()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
