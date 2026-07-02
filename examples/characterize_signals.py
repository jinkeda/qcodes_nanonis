"""Read-only live characterization of the Nanonis Signals polling path.

The script records slot names, cross-checks the configured Z slot through
``ValsGet``/``ValGet``/``ZPosGet``, compares both wait modes, and estimates the
observed float32 quantization step. It sends Get commands only.

Set ``Z_SIGNAL_INDEX`` for the rig, then run from the repository root::

    python examples/characterize_signals.py
"""

from __future__ import annotations

import json
import sys
import time
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

HOST = "127.0.0.1"
PORT = 6504
Z_SIGNAL_INDEX = 0  # Replace from the printed Signals.NamesGet table.
REPETITIONS = 100


def _vals(response: Any) -> np.ndarray:
    if not isinstance(response, dict):
        raise RuntimeError("Signals.ValsGet did not return a mapping")
    values = np.asarray(response["signals_values"], dtype=np.float64)
    if response["signals_values_size"] != values.size:
        raise RuntimeError("Signals.ValsGet returned an inconsistent size")
    return values


def _timed_vals(nanonis, wait: bool) -> dict[str, Any]:
    latencies: list[float] = []
    samples: list[float] = []
    arrivals: list[float] = []
    for _ in range(REPETITIONS):
        started = time.perf_counter()
        value = _vals(nanonis.send("Signals.ValsGet", 1, (Z_SIGNAL_INDEX,), int(wait)))[
            0
        ]
        arrivals.append(time.perf_counter())
        latencies.append(arrivals[-1] - started)
        samples.append(float(value))
    intervals = np.diff(arrivals)
    return {
        "wait_for_newest_data": wait,
        "latency_s": _distribution(latencies),
        "inter_arrival_s": _distribution(intervals),
        "values": samples,
    }


def _distribution(values) -> dict[str, float | int | None]:
    array = np.asarray(values, dtype=np.float64)
    if not array.size:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    return {
        "count": int(array.size),
        "min": float(np.min(array)),
        "median": float(np.median(array)),
        "p95": float(np.percentile(array, 95)),
        "max": float(np.max(array)),
    }


def _quantization_step(values: list[float]) -> float | None:
    unique = np.unique(np.asarray(values, dtype=np.float32))
    differences = np.diff(unique.astype(np.float64))
    positive = differences[differences > 0]
    return float(np.min(positive)) if positive.size else None


def characterize(nanonis) -> dict[str, Any]:
    names_response = nanonis.send("Signals.NamesGet")
    names = list(names_response["signals_names"])
    if names_response["signals_names_number"] != len(names):
        raise RuntimeError("Signals.NamesGet returned an inconsistent count")
    if Z_SIGNAL_INDEX >= len(names):
        raise RuntimeError("Z_SIGNAL_INDEX is outside the returned slot table")

    print("=== Signals slot table ===")
    for index, name in enumerate(names):
        print(f"{index:3d}: {name}")

    cross_checks: list[dict[str, float]] = []
    for _ in range(10):
        vals_z = float(
            _vals(nanonis.send("Signals.ValsGet", 1, (Z_SIGNAL_INDEX,), 1))[0]
        )
        val_z = float(nanonis.send("Signals.ValGet", Z_SIGNAL_INDEX, 1))
        zctrl_z = float(nanonis.send("ZCtrl.ZPosGet"))
        cross_checks.append(
            {
                "Signals.ValsGet": vals_z,
                "Signals.ValGet": val_z,
                "ZCtrl.ZPosGet": zctrl_z,
            }
        )

    no_wait = _timed_vals(nanonis, False)
    wait = _timed_vals(nanonis, True)
    observed = no_wait["values"] + wait["values"]
    observed_step = _quantization_step(observed)
    arrays = np.asarray(
        [[row[key] for key in row] for row in cross_checks], dtype=np.float64
    )
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": HOST,
        "port": PORT,
        "z_signal_index": Z_SIGNAL_INDEX,
        "z_signal_name": names[Z_SIGNAL_INDEX],
        "slot_names": names,
        "cross_checks": cross_checks,
        "cross_check_max_spread_m": float(np.max(np.ptp(arrays, axis=1))),
        "wait_mode_characterization": {"false": no_wait, "true": wait},
        "observed_float32_step_m": observed_step,
        "observed_step_below_1_pm": observed_step is None or observed_step < 1e-12,
        "float32_ulp_at_max_abs_z_m": float(
            np.spacing(np.float32(np.max(np.abs(observed))))
        ),
        "provisional_default_wait_for_newest_data": True,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ROOT / "reports" / f"signals_characterization_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nSaved:", path)
    print("Cross-check max spread (m):", report["cross_check_max_spread_m"])
    print("Observed float32 step (m):", report["observed_float32_step_m"])
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
        characterize(nanonis)
    finally:
        nanonis.disconnect()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
