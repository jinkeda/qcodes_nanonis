# Scan Vertical — Live Acceptance Gate Closure Plan

Status: proposed (rev. 1) · Date: 2026-07-01

The scan vertical's **code** is complete: `ScanWorkflow.run()` / `run_partial()`,
the shared toolkit generalizations (G1 `recover_module`, G2 `TipRestorePolicy`),
and the M4-D QCoDeS adapter ([`qcodes/scan.py`](../src/nanonis/qcodes/scan.py))
are all built and green (166 tests). Two of the three "Next milestone" items in
[`blueprint.md`](blueprint.md) are **done**: `FrameDataGrab` row orientation is
characterized (`row_order = "top_to_bottom"`, physically-indexed buffer) and wired
through the adapter.

This plan covers **only what remains to close the live acceptance gate** — the
work that is *not* pure coding and therefore was not finished by the
implementation. It is meant to be worked **alongside**
[`data_readers_plan.md`](data_readers_plan.md): item **G-3** below (a full
autosaved `run()`) produces the real `.sxm` file that the `.sxm` reader is
validated against, so the two plans share one live session.

## What is already closed (do not redo)

- **Row orientation** — `verify_row_orientation.py`, run up+down on the 6501 rig
  (2026-07-01), settled `row_order = "top_to_bottom"`, physically-indexed buffer.
- **`WaitEndOfLine` semantics** — ~2 returns/image row, 1-based `line_number`,
  variable startup transient; `run_partial` counts trace returns.
- **QCoDeS scan adapter** — acquire-first, 2-D index meshgrids + optional physical
  `x_m`/`y_m` grids from the confirmed `row_order`.
- **Command sequence order** — verified live by `characterize_oneframe.py`.

## Design rules (inherited, non-negotiable)

- **Mandatory preflight + approval gating.** No live scan runs against unapproved
  piezo limits; every characterization script pulls its policy through
  `rig_safety_policies.require_approved(...)`, which raises until sign-off.
- **Sample-independent methods preferred.** Where a characterization can be made
  independent of the surface (as row orientation was), do so; where it cannot
  (column order needs signal contrast), state the dependency explicitly and print
  the raw observations so a wrong assumption can be reinterpreted after the fact.
- **Preserve raw order in the domain model.** `ScanResult` keeps raw matrix order
  and the explicit controller scan direction; characterization changes the
  *interpretation* (`row_order`/`column_order` passed to `scan_coordinate_grids`),
  never the stored data.
- **Code changes from this gate are minimal.** The expected deltas are: a new
  `column_order` constant once verified, flipping `approved=True` in the rig
  registry, and small field-name corrections if a live response disagrees with
  the schema. No new workflow surface.

## Remaining items

### G-1 — Approve rig safety limits *(blocking; operator decision, not code)*

[`examples/rig_safety_policies.py`](../examples/rig_safety_policies.py) ships
`DEMO_6504` as `approved=False` (`0.1.0-draft`). Until a qualified operator signs
off, `require_approved("demo-6504")` raises and **no** live scan (G-2, G-3) can
run. This item is a review checklist, not an implementation task.

**Checklist to sign off (operator fills in and dates):**

| Field | Draft value | Confirm for this rig |
| --- | --- | --- |
| `measured_piezo_range_m` | (3.0e-6, 3.0e-6, 1.5e-6) | matches `Piezo.RangeGet`? |
| `piezo_safety_margin` | 100 nm | keeps frames clear of ±1.5 µm edges? |
| `max_pixels` / `max_lines` | 1024 / 1024 | raster cap acceptable? |
| `min_line_time` / `max_line_time` | 1e-3 / 10.0 s | bracket the slowest+fastest real scans? |
| `min_linear_speed` / `max_linear_speed` | 1e-12 / 1e-2 m/s | plausible bounds? |
| `tip` (`TipRestorePolicy`) | `None` | add only if scans should restore tunnel conditions |

**Acceptance:** operator sets `approved=True`, fills `approved_on` (ISO date),
bumps `version` (drop `-draft`), and records who approved it in `notes`. Add a
one-line test asserting `require_approved("demo-6504")` returns without raising
(guards against an accidental revert to draft), and confirm the rig `PORT`
(registry says 6504; live runs so far used 6501 — reconcile the rig id/port).

### G-2 — Characterize fast-axis `column_order` *(live hardware)*

The only remaining orientation unknown. `scan_coordinate_grids` and
`qcodes/scan.py` currently default `column_order = "left_to_right"` and log a
warning when physical grids are emitted (physical X may be mirrored until this is
settled). Index grids and all stored data are unaffected — this only fixes the
sign of the physical-X mapping.

**Why it's harder than rows.** `run_partial` fills whole *rows*, so the
row-orientation trick (partial fill → which matrix end) does not exist for
columns. Column order needs **signal contrast across the fast axis**, so the
method is **sample-dependent** — unlike G-1's row work.

> **Not derivable from piezo calibration.** `column_order` is purely a
> **matrix-index ↔ frame-local-physical** convention (which stored column is the
> frame's left/right edge) — a buffer *layout* fact. The piezo calibration sign
> (e.g. Calib X = −8.322e-9 m/V in `FGT_0030.sxm`) is a **voltage ↔ physical**
> mapping and is a different concern: geometry works entirely in meters (Nanonis
> already applied the calibration to the reported scanfield), so the sign never
> enters `scan_coordinate_grids`. And since the buffer is physically-indexed (from
> the row result), column order is almost certainly a single fixed convention, not
> derived from scan mechanics. It still must be *measured* by the correlation check
> below, not inferred from the header.

**Method (`examples/verify_column_orientation.py`, new).** Acquire the *same*
line's **forward and backward** images of a frame that has lateral signal
variation (any non-uniform surface, or deliberately a tilted/feature-bearing
area):

- If the buffer is **physically indexed** on the fast axis, `forward[i, j]` and
  `backward[i, j]` sample the **same physical column** → the two images correlate
  **directly** (peak at zero lateral shift), and matrix column 0 is a fixed
  physical edge. Combined with the GUI's known trace direction, that fixes
  `column_order`.
- If **acquisition-ordered**, `backward` is the **column-reverse** of `forward`
  → they correlate only after `np.fliplr`.

> **Prior evidence from `spaik`.** `spaik`'s `.sxm` reader flips the **backward**
> image horizontally to align it with the forward image
> ([SXM.py:184-186](../../spaik/src/spaik/Utilities/SXM.py#L184-L186)) — i.e. in the
> saved file `backward = fliplr(forward)`. That is the *acquisition-ordered fast
> axis* case above, and it is battle-tested domain knowledge for the **file**. It
> gives G-2 a strong expected answer, but does **not** close it: `spaik` describes
> the saved `.sxm`, whereas G-2 characterizes the live `FrameDataGrab` buffer, which
> may order the fast axis differently. So use it as the expected result to confirm,
> not as a substitute for the live check.

Reuse `verify_row_orientation.py`'s structure exactly: a pure, offline-testable
analysis (`classify_column_model(forward, backward) -> verdict`) with a `SELFTEST`
on synthetic mirror/non-mirror pairs, a `CONFIRMATION_TOKEN`-gated live path that
pulls the approved policy, `angle=0` so matrix columns coincide with screen
left/right, and a printed raw-observation report so a wrong GUI assumption is
reinterpretable. State the one mapping assumption explicitly (which physical edge
a *forward/trace* line starts from, per the GUI), mirroring `UP_STARTS_AT`.

**Acceptance:**
1. Two live runs agree on the buffer model and a single `column_order`.
2. Add the confirmed value as `DEFAULT_COLUMN_ORDER` in `qcodes/scan.py` (replacing
   the assumed default) and drop/soften the "X may be mirrored" warning to reflect
   the now-verified axis. Update the walkthrough's "Still uncharacterized" notes.
3. The pure analysis is unit-tested offline (mirror, non-mirror, low-contrast
   inconclusive cases), same as `summarize_line_records` / `classify_finite_block`.

> If the installed surface has no usable lateral contrast, G-2 stalls on sample
> availability, not on code — record that and ship physical grids with the
> documented default + warning until a suitable frame exists. Index-grid
> persistence is unaffected, so this does **not** block G-3 or the data readers.

### G-3 — Full autosaved `run()` end-to-end *(live hardware; produces the reader oracle)*

Everything live so far used `run_partial` (autosave off, `saved_path == ""`). The
full-frame contract — `WaitEndOfScan` completion, a non-empty `saved_path`, and
the saved `.sxm` on disk — has **not** been exercised end to end on hardware. This
is the last piece of `run()`'s own acceptance, and its output is the input the
`.sxm` reader is validated against.

**Method (`examples/verify_full_run.py`, new — or extend `characterize_oneframe.py`).**
One small, approved-policy frame at `angle=0` with `autosave="next"` and
`data_directions=("forward", "backward")`:

1. `ScanWorkflow(...).run(config, region)` to natural completion.
2. Assert `result.saved_path` is non-empty and the file exists on disk.
3. Record: the full command sequence (compare to `characterize_oneframe.py`), the
   grabbed matrix dimensions vs effective buffer dims (the walkthrough warns these
   may differ — confirm), per-channel×direction shapes, and module returns to idle.
4. **Keep the saved `.sxm`** as a committed test fixture (see
   [`data_readers_plan.md`](data_readers_plan.md) D0) — this is the file whose
   in-file orientation the reader must match against this same run's in-memory
   `ScanResult` (D1 acceptance).

**Acceptance:**
1. Full `run()` completes, `saved_path` non-empty, file present, module idle.
2. Command order matches the characterized sequence; any grabbed-vs-effective
   dimension mismatch is explained (clipping/orientation) and the schema field
   names reconciled if a response disagrees (G-4 folds in here).
3. The saved `.sxm` + the serialized `ScanResult` (channels, `requested_region`,
   `row_order`) are archived together as the reader oracle.

### G-4 — Live field alignment & `PropsGet` autopaste encoding *(minor; opportunistic)*

Fold into the G-2/G-3 sessions rather than a separate run. During those live runs,
dump and confirm every `Scan.FrameGet` / `BufferGet` / `PropsGet` / `SpeedGet`
response field against the registry schema, and settle the live `PropsGet`
autopaste enum (currently only the read side is trusted). Correct any field-name
or type disagreement in the registry + snapshot code (small, test-backed edit).

**Acceptance:** every Frame/Buffer/Props/Speed field the snapshot reads is
confirmed against a live response; the autopaste encoding is recorded in the
walkthrough; any correction lands with a schema regression test.

### Coordination note — shared-primitive extraction (owned by the data-readers plan)

[`data_readers_plan.md`](data_readers_plan.md) D0 extracts `RowOrder`,
`ColumnOrder`, `scan_coordinate_grids`, `NaNPolicy`, and a `FrameGeometry` factored
out of `ScanRegion` into a neutral `nanonis.geometry` / `nanonis.types`, then
updates the `workflows/scan/*` and `qcodes/scan.py` import sites (166 tests stay
green). That is a **scan-vertical refactor**, so land it on a quiet tree — do it
either before or well after G-2/G-4's small schema edits, not interleaved, to avoid
two changes fighting over the same scan files. The characterization scripts here
(`verify_column_orientation.py`, `verify_full_run.py`) should import geometry
symbols from wherever they live at the time; after the extraction, that's
`nanonis.geometry`.

## Ordering and linkage to the data-readers plan

```
G-1 (approve policy)  ──►  gates all live runs
        │
        ├──►  G-2 (column_order)      ──►  fixes physical-X sign (adapter default)
        │
        └──►  G-3 (full autosaved run) ──►  saved .sxm  ─────────────┐
                    │                                                 ▼
                    └──►  G-4 (field alignment, PropsGet)   data_readers_plan D1:
                                                            .sxm reader orientation
                                                            validated against this
                                                            run's ScanResult
```

Do **G-1 first** (unblocks everything). Then a single live session runs **G-3**
(the fixture-producing full run) with **G-4** folded in, and **G-2** if a
contrast-bearing surface is available. The saved `.sxm` from G-3 hands off to the
data-readers plan. None of the code deltas here are large; the value of this plan
is sequencing the human/hardware-gated steps and tying them to the reader work.

## Acceptance criteria for closing the gate (summary)

- [ ] `rig_safety_policies` `demo-*` entry `approved=True`, dated, version bumped,
      rig id/port reconciled (G-1).
- [ ] `column_order` confirmed by two live runs and wired as the adapter default,
      or explicitly deferred on documented sample-contrast grounds (G-2).
- [ ] Full `run()` completes with a non-empty `saved_path` and an on-disk `.sxm`
      matching the in-memory `ScanResult`; command order re-confirmed (G-3).
- [ ] Every Frame/Buffer/Props/Speed field and the `PropsGet` autopaste encoding
      confirmed live; corrections land with regression tests (G-4).
- [ ] Saved `.sxm` + `ScanResult` archived as the `data/readers/sxm.py` oracle.

## References

- [`blueprint.md`](blueprint.md) — Next milestone (items 1–3).
- [`scan_workflow_walkthrough.md`](scan_workflow_walkthrough.md) — what's built and
  the 2026-07-01 orientation addenda.
- [`examples/verify_row_orientation.py`](../examples/verify_row_orientation.py) —
  the template for `verify_column_orientation.py` (G-2).
- [`data_readers_plan.md`](data_readers_plan.md) — consumes G-3's saved `.sxm`.
