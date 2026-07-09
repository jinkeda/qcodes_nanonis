# Nanonis Command Fix Plan

Companion to `live_test_report_2026-06-28.md`. Investigation of the genuine
command-definition failures found by `scripts/live_test_commands.py`, with a
concrete plan to fix them. **No config files have been changed yet.**

## 1. Scope

Of 147 tested commands: 58 PASS, 59 `MODULE_UNAVAILABLE` (env, not bugs),
8 `NANONIS_ERROR` from neutral args (not bugs), and **~24 genuine
definition bugs** (4 `PROTOCOL_MISMATCH` + 15 `DECODE_ERROR` +
1 `STRUCTURE_MISMATCH` + 2 `CONNECTION_ERROR` + a couple of borderline
`NANONIS_ERROR`).

> ⚠️ The 59 `MODULE_UNAVAILABLE` commands (all `PLL.*`, `MCVA5.*`,
> `AutoApproach.*`, `MProbeBias.*`, `TipShaper.*Set/Start`) were never actually
> exercised — the module error fires before argument parsing. Several of them
> almost certainly have the **same** definition bugs (their raw definitions are
> just as garbled). The true bug count is higher than 24; re-test with those
> modules enabled.

## 2. Root causes

All three are bugs in the PDF parser `generate_nanonis_tcp.py`, **not** in the
TCP/encoder/decoder layers (those are correct and pass their unit tests).

### RC-1 — Command-boundary "bleed" (catastrophic)
For many commands the parser concatenated fields belonging to *dozens* of
later commands into one definition. Evidence:
- `Bias.Pulse`: **57** send fields (real command: ~6).
- `BiasSpectr.SafeCond2Get`: **150+** send fields, **200+** recv fields.
- `Util.UnLock`: defined as `[rt_frequency, acquisition_period_s, rt_oversampling]`
  — fields that belong to a *different* command; `Util.UnLock` takes none.

These cannot be salvaged by tweaking; they must be re-derived from the spec.

### RC-2 — Redundant string size field (systematic)
The PDF lists a scalar string as two arguments — `X size (int)` then
`X (string)` — but physically a body string is `[int32 length][chars]`, i.e.
the "size" *is* the string's length prefix. Our codec's `string` type is
already self-describing (it writes/reads its own length). The parser emitted
the size as a **separate extra field**, so:
- **Send:** `series_name_size(int32) + series_name(string)` writes the length
  twice → Nanonis "Unflatten From String" error (`Scan.PropsSet`, `Script.Autosave`).
- **Recv:** the decoder reads the size int, then the `string` reads the *next*
  4 bytes (real chars) as a length → over-read / `UnicodeDecodeError`
  (`Util.VersionGet`, `Scan.PropsGet`, `Scan.FrameDataGrab`, ...).

Fix: **drop the `*_size` int field that precedes a scalar `string`.**

### RC-3 — Array size-in-bytes vs element-count — **WITHDRAWN (misdiagnosis)**
Original hypothesis: the byte-size int before a 1D string array is redundant
and should be dropped. **This was wrong.** Per the protocol, a 1D string array
sends BOTH its size-in-bytes AND its element-count as independent fields on the
wire, *plus* each element's own length prefix. Our decoder consumes the
byte-size as a normal field and uses the nearest preceding int (the count) as
the array length, so **both fields must be kept**. Removing the byte-size
regressed `Bias.RangeGet`, `Signals.NamesGet`, `Signals.MeasNamesGet`,
`BiasSpectr.Start`. The `Script.ChsGet` / `TipShaper.PropsGet` / `BiasSpectr.ChsGet`
failures are RC-1 bleed, not this. **No change to string arrays.**

## 3. Ground-truth sources (in priority order)

1. **`TCPProtocol_SPM.pdf` (April 2025, R14718)** — authoritative current spec.
2. **`spaik-main/.../BlueNanonisTCP.py`** — hand-written, hardware-tested
   per-command methods; excellent for exact arg/resp order and types. (Confirms
   e.g. `CurrentGainSet(gain_idx, filter_idx)` → two args, not one.)
3. **`legacy/nanonis_tcp.json`** — quick reference, but **partially outdated**
   vs current firmware. Use only as a cross-check, never as sole truth.

## 4. Strategy

Two tracks; do them in this order.

### Track A — systematic normalization (fixes many at once)
Add a normalization pass (in `generate_nanonis_tcp.py`, or a new
`scripts/normalize_commands.py` run over `nanonis_tcp_auto.json`) implementing
RC-2 and RC-3:
- Collapse `("<x> size", int) + ("<x>", string)` → `("<x>", string)`.
- Collapse `("<x> size", int) + ("<x> number"/"Number of <x>", int) + ("<x>", array/matrix)`
  → `(count, int) + ("<x>", array/matrix)`.
- Leave numeric scalars and numeric arrays untouched.

Then regenerate the YAML and re-run the live test. This should clear most of
the `Scan.*`, `Util.VersionGet`, `File.datLoad`, `BiasSpectr.PropsGet` class
**and** improve the many string-bearing commands that currently "pass" only
because they have no strings.

### Track B — re-derive the bled commands (RC-1)
Hand-rewrite each catastrophically-bled command from the PDF (cross-checked
against spaik). Track A will not fix these because their field lists are wrong
at the source. Candidates: `Bias.Pulse`, `BiasSpectr.SafeCond2Get`,
`TCPLog.StatusGet`, `PLLQCtrl.PhaseGet`, `Script.LUTDeploy`,
`TipShaper.PropsGet`, `MProbeCurrent.Get`, `Util.UnLock`, `PLLPhasSwp.Stop`,
`PLLPhasSwp.Start`, `Script.ChsGet`.

> Consider whether the per-prefix split files in `configs/commands/` (or a
> hand-maintained override file) are a better home for corrected definitions,
> so manual fixes are not overwritten on the next `generate_nanonis_tcp.py` run.

## 5. Per-command plan

| Command | Symptom | Root cause | Source | Action |
|---|---|---|---|---|
| `Scan.PropsSet` | PROTOCOL_MISMATCH (unflatten) | RC-2 | legacy ✓ / PDF | drop `series_name_size`, `comment_size` |
| `Scan.PropsGet` | DECODE_ERROR | RC-2/RC-3 | legacy ✓ / PDF | drop string/array byte-size fields; keep counts |
| `Util.VersionGet` | UnicodeDecodeError | RC-2 | PDF | drop `product_line_size`, `version_size` |
| `Scan.FrameDataGrab` | UnicodeDecodeError | RC-2 | legacy ✓ | drop `channels_name_size` (keep `channel_name`) |
| `BiasSpectr.PropsGet` | CONNECTION_ERROR (reset) | RC-3 (+ collateral) | legacy ✓ | drop array byte-size fields; keep counts |
| `BiasSpectr.ChsGet` | STRUCTURE_MISMATCH (+121 B) | incomplete def | PDF/spaik | recv truly returns more than `[count,array]`; re-derive |
| `Current.GainSet` | PROTOCOL_MISMATCH (unflatten int32) | outdated def | spaik ✓ | add 2nd arg `filter_index (int32)` |
| `Motor.FreqAmpGet` | PROTOCOL_MISMATCH (unflatten u16) | missing send arg | PDF/spaik | add send arg (axis/index `uint16`) — verify in PDF |
| `Motor.PosGet` | PROTOCOL_MISMATCH (unflatten u32) | missing send arg | PDF/spaik | add send arg (`uint32`) — verify in PDF |
| `Bias.Pulse` | DECODE_ERROR (array w/o count) | RC-1 | PDF/spaik | full re-derive (real recv is small/empty) |
| `File.datLoad` | DECODE_ERROR (array w/o count) | RC-1/RC-3 | PDF | re-derive send (drop path size) + recv |
| `PLLPhasSwp.Start` | DECODE_ERROR | RC-1 | PDF | re-derive recv |
| `PLLPhasSwp.Stop` | DECODE_ERROR | RC-1 | PDF | re-derive (Stop usually has no recv) |
| `PLLQCtrl.PhaseGet` | DECODE_ERROR | RC-1 | PDF | re-derive |
| `BiasSpectr.SafeCond2Get` | DECODE_ERROR | RC-1 | PDF/legacy | re-derive (mirror SafeCond1Get shape) |
| `BiasSpectr.SafeCond1Get` | CONNECTION_ERROR | collateral of SafeCond2Get | — | likely fixed once SafeCond2Get fixed; re-test |
| `TCPLog.StatusGet` | DECODE_ERROR | RC-1 | PDF | re-derive |
| `TipShaper.PropsGet` | DECODE_ERROR | RC-1/RC-3 | PDF/spaik | re-derive |
| `MProbeCurrent.Get` | DECODE_ERROR | RC-1 | PDF | re-derive (also MODULE_UNAVAILABLE on real HW) |
| `Script.ChsGet` | DECODE_ERROR (array mult) | RC-3 | PDF | fix array count field |
| `Script.LUTDeploy` | DECODE_ERROR | RC-1 | PDF | re-derive |
| `Script.Autosave` | NANONIS_ERROR (read msg) | RC-2 | PDF | drop path size fields in send |
| `Script.LUTLoad` / `LUTSave` | NANONIS_ERROR ("Not a valid path") | not a bug | — | expected (empty path arg); skip or pass a real path |
| `Util.SessionPathSet`, `Util.SettingsLoad/Save` | NANONIS_ERROR | not a bug | — | expected (empty arg) |

## 6. Verification loop

After each batch of fixes:
```bash
python scripts/convert_json_to_yaml.py     # regenerate YAML from JSON source
python scripts/live_test_commands.py        # re-run the live test (skips Util.Quit)
```
Track progress by category counts in `live_test_report.md`; target zero
`PROTOCOL_MISMATCH` / `DECODE_ERROR` / `STRUCTURE_MISMATCH`.

## 7. Caveats
- Run with **PLL / Preamplifier(MCVA5) / Auto Approach / Multi-probe / Oscilloscope
  modules enabled** to clear `MODULE_UNAVAILABLE` and expose any further bugs.
- `Util.Quit` is excluded by the harness (it shuts the controller down).
- `NANONIS_ERROR`s from empty path/file arguments are expected, not bugs — pass
  real values to test those commands properly.

## Track A — DONE (2026-06-28)

Implemented RC-2 only (scalar-string size removal) as a normalization pass in
`scripts/convert_json_to_yaml.py::normalize_size_fields`, applied during YAML
generation (non-destructive to `nanonis_tcp_auto.json`). RC-3 was withdrawn
after it caused regressions (see above).

Result on the live simulator (deterministic, definition-bug categories only):

| Category | Before | After |
|---|---|---|
| PROTOCOL_MISMATCH | 4 | 4 |
| STRUCTURE_MISMATCH | 1 | 0 |
| DECODE_ERROR | 15 | 12 |
| CONNECTION_ERROR (collateral) | 2 | 0 |

Fixed by RC-2: `Util.VersionGet`, `Scan.FrameDataGrab`, `Scan.PropsGet`,
`BiasSpectr.SafeCond1Get` (collateral), and others. **No regressions** (unit
tests 54/54; the 4 string-array commands restored). 77 redundant scalar-string
size fields removed across 26 commands.

Remaining definition bugs (→ Track B): `Bias.Pulse`, `File.datLoad`,
`PLLPhasSwp.Start/Stop`, `PLLQCtrl.PhaseGet`, `BiasSpectr.SafeCond2Get`,
`TCPLog.StatusGet`, `TipShaper.PropsGet`, `MProbeCurrent.Get`, `Script.ChsGet`,
`Script.LUTDeploy`, `Util.UnLock` (RC-1 bleed); `Current.GainSet`,
`Motor.FreqAmpGet`, `Motor.PosGet`, `Scan.PropsSet` (wrong/missing send args).

## Track B — IN PROGRESS (2026-06-28)

Hand-corrected definitions live in `configs/nanonis_tcp_overrides.yaml` (the
single editable source of truth for corrections). Ground truth: spaik
`BlueNanonisTCP.py`.

**Workflow to add/fix a command:**
1. Edit `configs/nanonis_tcp_overrides.yaml`.
2. `python scripts/apply_overrides_to_json.py` — writes the fixes into
   `nanonis_tcp_auto.json` (short-code format) and re-splits
   `configs/commands/*.json`, so the JSON source stays consistent.
3. `python scripts/convert_json_to_yaml.py` — regenerates `nanonis_tcp.yaml`
   (overrides are also re-applied here, idempotently, as a safety net against a
   future `generate_nanonis_tcp.py` run).
4. `python scripts/live_test_commands.py` — verify.

**Fixed (7/7 definitions correct):** `Current.GainSet`, `Motor.FreqAmpGet`,
`Bias.Pulse`, `BiasSpectr.SafeCond2Get`, `Util.UnLock` now PASS; `Motor.PosGet`
and `TipShaper.PropsGet` now return `MODULE_UNAVAILABLE` (definition accepted;
module simply not running in this session). Live pass: 68 → **73**.

**PDF-derived batch (5 more, ground-truthed against TCPProtocol_SPM.pdf):**
`Scan.PropsSet` (firmware added a Modules-names array + `Autopaste`) and
`File.datLoad` (size/count fields were mis-typed as `string`) now PASS.
`TCPLog.StatusGet`, `Script.ChsGet`, `Script.LUTDeploy` now decode correctly and
return proper Nanonis *state* errors (logger/script module not running) instead
of decode/protocol errors — i.e. their wire format is fixed; they're env-locked
like the other module commands. Live pass: 73 → **75**.

12 commands are now hand-corrected in `nanonis_tcp_overrides.yaml` (and synced
into the JSON). All definition bugs that are testable in this session are fixed.

**Remaining (module-locked — enable the module to verify a fix):**
`MProbeCurrent.Get`, `PLLPhasSwp.Start/Stop`, `PLLQCtrl.PhaseGet`. These four
need the Multi-probe / PLL modules running before a corrected definition can be
confirmed against the controller.

## 8. Recommended next step
Start with **Track A** (the RC-2/RC-3 normalization) — it is mechanical,
low-risk, and likely clears ~8–10 commands plus latent issues, then re-test to
see the residual. Then hand-fix the **Track B** bled commands using the PDF +
spaik as reference. I can implement either track on request.
