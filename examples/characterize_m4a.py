"""M4-A read-only scan characterization against a real Nanonis controller.

Records the raw Frame/Buffer/Props/Speed responses, piezo range, signal names,
and scan status, then grabs the **currently buffered** frame forward and backward
for every buffered channel and reports orientation evidence. It does NOT write
settings and does NOT start a scan -- every command here is a Get or a
FrameDataGrab, which read existing controller state only (see the live notebook,
section 4). The tip does not move.

Outputs:
- prints a human-readable summary, and
- saves the raw responses (JSON) and grabbed arrays (NPZ) next to this script,
  timestamped, so the orientation can be compared against the controller GUI.

Usage:
    python characterize_m4a.py            # connects to HOST:PORT below
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if not (ROOT / "src" / "nanonis").exists():
    ROOT = ROOT.parent
if not (ROOT / "src" / "nanonis").exists():  # pragma: no cover - import guard
    raise RuntimeError("Run from the repository root or examples directory")
sys.path.insert(0, str(ROOT / "src"))

from nanonis.command import NanonisController  # noqa: E402
from nanonis.workflows.scan import ScanSettings  # noqa: E402

HOST = "127.0.0.1"
PORT = 6504  # 6503 is typically held by the live-demo notebook kernel
DATA_FORWARD = 1
DATA_BACKWARD = 0


def _jsonable(value):
    """Make controller responses JSON-serializable (arrays -> lists)."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def grab(nanonis, channel_index, direction):
    return nanonis.send("Scan.FrameDataGrab", channel_index, direction)


def orientation_evidence(forward: np.ndarray, backward: np.ndarray) -> dict:
    """Read-only statistics that hint at fast/slow axis orientation.

    None of these *prove* physical orientation -- that needs a known feature or
    the GUI -- but they flag the usual fast-axis (column) reversal between trace
    and retrace, and show the slow-axis (row) trend.
    """
    fwd = np.asarray(forward, dtype=float)
    bwd = np.asarray(backward, dtype=float)
    out: dict = {"shape": list(fwd.shape)}
    finite = np.isfinite(fwd) & np.isfinite(bwd)
    out["finite_pixels"] = int(finite.sum())
    if finite.sum() < 4 or fwd.shape != bwd.shape:
        out["note"] = "too few finite pixels (or shape mismatch) for correlation"
        return out

    def corr(a, b):
        a = a[finite]
        b = b[finite]
        if a.std() == 0 or b.std() == 0:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    out["corr_forward_backward"] = corr(fwd, bwd)
    # If the backward image is the trace reversed along the fast (column) axis,
    # flipping its columns should correlate much more strongly.
    out["corr_forward_backward_colflipped"] = corr(fwd, np.fliplr(bwd))
    # Slow-axis (row) trend: mean per row, first vs last finite row.
    row_means = np.nanmean(np.where(np.isfinite(fwd), fwd, np.nan), axis=1)
    finite_rows = np.where(np.isfinite(row_means))[0]
    if finite_rows.size:
        out["first_finite_row"] = int(finite_rows[0])
        out["last_finite_row"] = int(finite_rows[-1])
        out["row_mean_first"] = float(row_means[finite_rows[0]])
        out["row_mean_last"] = float(row_means[finite_rows[-1]])
    return out


def characterize(nanonis) -> dict:
    record: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": HOST,
        "port": PORT,
    }

    # --- Raw read-only responses ---
    raw = {
        "Piezo.RangeGet": nanonis.send("Piezo.RangeGet"),
        "Scan.StatusGet": nanonis.send("Scan.StatusGet"),
        "Scan.FrameGet": nanonis.send("Scan.FrameGet"),
        "Scan.BufferGet": nanonis.send("Scan.BufferGet"),
        "Scan.PropsGet": nanonis.send("Scan.PropsGet"),
        "Scan.SpeedGet": nanonis.send("Scan.SpeedGet"),
    }
    signals = nanonis.send("Signals.NamesGet")
    names = list(signals["signals_names"])
    record["raw_responses"] = {k: _jsonable(v) for k, v in raw.items()}

    print("=== M4-A read-only characterization ===")
    print("Scan status (0=idle):", raw["Scan.StatusGet"])
    print("Piezo range (m):", raw["Piezo.RangeGet"])
    print("Frame:", raw["Scan.FrameGet"])
    print("Buffer:", raw["Scan.BufferGet"])
    print("Props:", raw["Scan.PropsGet"])
    print("Speed:", raw["Scan.SpeedGet"])
    print("Raw autopaste value (confirm encoding):",
          raw["Scan.PropsGet"].get("autopaste"))

    # Typed snapshot for convenience (read-only).
    settings = ScanSettings.snapshot(nanonis)
    channels = list(settings.channels)
    record["channels"] = channels
    record["channel_names"] = [names[c] if c < len(names) else f"?{c}" for c in channels]
    print("\nBuffered channels:", record["channel_names"])
    print(f"Buffer dims: {settings.lines} lines x {settings.pixels} pixels")

    # --- Forward/backward grab orientation (read-only buffer reads) ---
    arrays: dict = {}
    record["orientation"] = {}
    print("\n--- Forward/backward grab orientation (current buffer) ---")
    for channel_index in channels:
        fwd_resp = grab(nanonis, channel_index, DATA_FORWARD)
        bwd_resp = grab(nanonis, channel_index, DATA_BACKWARD)
        fwd = np.asarray(fwd_resp["scan_data"], dtype=float)
        bwd = np.asarray(bwd_resp["scan_data"], dtype=float)
        name = str(fwd_resp.get("channel_name", channel_index))
        arrays[f"ch{channel_index}_forward"] = fwd
        arrays[f"ch{channel_index}_backward"] = bwd
        ev = orientation_evidence(fwd, bwd)
        ev["channel_name"] = name
        ev["wire_scan_direction_forward"] = int(fwd_resp.get("scan_direction", -1))
        record["orientation"][str(channel_index)] = ev
        print(f"  [{channel_index}] {name}: shape={ev['shape']} "
              f"finite={ev['finite_pixels']} "
              f"corr(fwd,bwd)={ev.get('corr_forward_backward')!r} "
              f"corr(fwd,fliplr bwd)={ev.get('corr_forward_backward_colflipped')!r}")

    # --- Persist for GUI comparison ---
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = ROOT / "examples" / f"m4a_characterization_{stamp}.json"
    if not json_path.parent.exists():
        json_path = ROOT / f"m4a_characterization_{stamp}.json"
    npz_path = json_path.with_suffix(".npz")
    json_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    np.savez_compressed(npz_path, **arrays)
    print("\nSaved raw responses + orientation summary:", json_path.name)
    print("Saved grabbed arrays:", npz_path.name)
    record["json_path"] = str(json_path)
    record["npz_path"] = str(npz_path)
    return record


def main() -> int:
    nanonis = NanonisController(host=HOST, port=PORT,
                               config_path=ROOT / "configs" / "commands", timeout=10.0)
    nanonis.connect()
    print("Connected:", nanonis.is_connected, "(read-only session)")
    try:
        characterize(nanonis)
    finally:
        nanonis.disconnect()
        print("Disconnected:", not nanonis.is_connected)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
