"""Step 2 + orientation: one conservative full-frame acquisition on hardware.

Runs ``ScanWorkflow.run`` once on a small, conservative frame while recording the
exact command sequence, so the start -> wait -> grab -> restore event order can be
verified. The completed result also carries the forward and backward images, which
give the fast-axis (trace/retrace) orientation evidence that the read-only M4-A
buffer could not (it was empty).

SAFETY: this STARTS A SCAN and MOVES THE TIP. Read scan_workflow_live_demo.ipynb
first and replace placeholders with rig-approved values. It runs only with the
confirmation token::

    python characterize_oneframe.py RUN_ONEFRAME
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
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
from nanonis.workflows import NaNPolicy, StateRestorationError  # noqa: E402
from nanonis.workflows.scan import ScanResult, ScanWorkflow, scan  # noqa: E402

# Reuse the characterization helpers (conservative config + safety policy).
_spec = importlib.util.spec_from_file_location("vw", ROOT / "examples" / "verify_waitendofline.py")
vw = importlib.util.module_from_spec(_spec)
sys.modules["vw"] = vw
_spec.loader.exec_module(vw)

HOST = "127.0.0.1"
PORT = 6504
CONFIRMATION_TOKEN = "RUN_ONEFRAME"


def instrument(nanonis):
    """Wrap nanonis.send to record (command, args) in call order."""
    events: list[tuple[str, tuple]] = []
    original = nanonis.send

    def recording_send(command, *args, timeout=None, check_error=True):
        events.append((command, args))
        return original(command, *args, timeout=timeout, check_error=check_error)

    nanonis.send = recording_send
    return events


def summarize_event_order(events: list[tuple[str, tuple]]) -> dict:
    names = [c for c, _ in events]

    def first(pred):
        return next((i for i, n in enumerate(names) if pred(n)), None)

    action_idxs = [i for i, (c, _) in enumerate(events) if c == "Scan.Action"]
    start_idx = next((i for i in action_idxs if events[i][1][:1] == (0,)), None)
    stop_idx = next((i for i in action_idxs if events[i][1][:1] == (1,)), None)
    wait_idx = first(lambda n: n == "Scan.WaitEndOfScan")
    grab_idx = first(lambda n: n == "Scan.FrameDataGrab")
    # Restoration setters appear after the grabs.
    restore_idx = next(
        (i for i, (c, _) in enumerate(events)
         if c.endswith("Set") and grab_idx is not None and i > grab_idx),
        None,
    )
    return {
        "total_commands": len(events),
        "start_index": start_idx,
        "wait_index": wait_idx,
        "grab_index": grab_idx,
        "stop_index": stop_idx,  # None on a clean run: no recovery stop needed
        "first_restore_set_index": restore_idx,
        "order_ok": (
            start_idx is not None and wait_idx is not None and grab_idx is not None
            and start_idx < wait_idx < grab_idx
            and (restore_idx is None or grab_idx < restore_idx)
        ),
        "recovery_stop_issued": stop_idx is not None,
    }


def orientation_from_result(result: ScanResult) -> dict:
    fwd_img = next((im for im in result.images if im.direction == "forward"), None)
    bwd_img = next((im for im in result.images if im.direction == "backward"), None)
    if fwd_img is None or bwd_img is None:
        return {"note": "need both forward and backward images"}
    fwd = np.asarray(fwd_img.data, dtype=float)
    bwd = np.asarray(bwd_img.data, dtype=float)
    finite = np.isfinite(fwd) & np.isfinite(bwd)

    def corr(a, b):
        a, b = a[finite], b[finite]
        if a.size < 4 or a.std() == 0 or b.std() == 0:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    row_means = np.nanmean(fwd, axis=1)
    return {
        "shape": list(fwd.shape),
        "finite_pixels": int(finite.sum()),
        "wire_scan_direction": fwd_img.scan_direction,
        "corr_forward_backward": corr(fwd, bwd),
        # A markedly higher value here means the backward image is the trace
        # reversed along the fast (column) axis -- the usual retrace convention.
        "corr_forward_backward_colflipped": corr(fwd, np.fliplr(bwd)),
        "row_mean_first": float(row_means[0]),
        "row_mean_last": float(row_means[-1]),
    }


def run(nanonis) -> dict:
    safety_policy = vw.build_safety_policy()
    # Grab both directions so forward/backward orientation can be compared.
    config = replace(vw.build_config(), data_directions=("forward", "backward"))
    events = instrument(nanonis)

    print(f"Running one full frame ({config.pixels}x{config.lines}, "
          f"width {config.width*1e9:.1f} nm)...", flush=True)
    try:
        result = ScanWorkflow(nanonis, safety_policy=safety_policy,
                              nan_policy=NaNPolicy.WARN).run(config)
    except StateRestorationError as exc:
        print("STATE RESTORATION FAILED:", exc)
        if exc.result is None:
            raise
        result = exc.result

    order = summarize_event_order(events)
    orient = orientation_from_result(result)

    print("\n--- Event order ---")
    print("command sequence:", " -> ".join(c for c, _ in events))
    for key, val in order.items():
        print(f"  {key}: {val}")
    print("saved_path:", repr(result.saved_path), "(empty is expected with autosave='off')")
    print("acquisition_duration:", result.acquisition_duration, "s")

    print("\n--- Orientation evidence (forward vs backward) ---")
    for key, val in orient.items():
        print(f"  {key}: {val}")
    if orient.get("corr_forward_backward_colflipped", -2) > orient.get("corr_forward_backward", 2):
        print("  => backward looks like the column-reversed trace (fast-axis reversal).")

    # Persist for the record.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "examples" / f"oneframe_characterization_{stamp}.json"
    if not out.parent.exists():
        out = ROOT / f"oneframe_characterization_{stamp}.json"
    npz = out.with_suffix(".npz")
    out.write_text(json.dumps({
        "timestamp_utc": stamp,
        "command_sequence": [c for c, _ in events],
        "event_order": order,
        "orientation": orient,
        "saved_path": result.saved_path,
        "acquisition_duration_s": result.acquisition_duration,
    }, indent=2), encoding="utf-8")
    np.savez_compressed(npz, **{
        f"{im.direction}": np.asarray(im.data) for im in result.images
    })
    print("\nSaved:", out.name, "and", npz.name)
    return {"order": order, "orientation": orient}


def main(argv: list[str]) -> int:
    if CONFIRMATION_TOKEN not in argv[1:]:
        print("Refusing to start: this moves the tip and runs a scan.\n"
              f"Re-run with: python {Path(__file__).name} {CONFIRMATION_TOKEN}")
        return 1
    nanonis = NanonisController(host=HOST, port=PORT,
                               config_path=ROOT / "configs" / "commands", timeout=10.0)
    nanonis.connect()
    print("Connected:", nanonis.is_connected)
    try:
        run(nanonis)
    finally:
        nanonis.disconnect()
        print("Disconnected:", not nanonis.is_connected)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main(sys.argv))
