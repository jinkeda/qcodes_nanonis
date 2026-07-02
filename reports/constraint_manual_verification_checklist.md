# Constraint Overlay Manual Verification Checklist

Manual review targets for `configs/command_constraints.json`, ordered by risk.

How the risk is ranked:

- Constraints reproduce the exact sizes the old trailing-integer heuristic used, so
  any command that already ran successfully on real hardware is implicitly
  validated. The risk concentrates in commands that were annotated but never
  exercised.
- Receive-side mistakes fail loudly: the decoder's byte accounting raises a
  protocol error instead of returning shifted data. Send-side mistakes transmit a
  malformed command to the instrument, so send-side entries come first.
- For any receive command that can be triggered safely, one live call is a
  stronger check than reading the PDF: a wrong annotation now raises immediately.

## Tier 1 — Send side, never exercised; a wrong annotation malforms a command

- [ ] `Script.LUTLoad` — Is "LUT values size" the **element count** or the
  **byte count** of the float32 array? If bytes, inference and validation are
  both wrong by 4x.
- [ ] `DigLines.Pulse` — Same question for "Digital lines size". For a uint8
  array bytes equal elements, so likely harmless either way; confirm and note it.
- [ ] `DataLog.PropsSet` / `Scan.PropsSet` / `HSSwp.SaveOptionsSet` /
  `GenSwp.AcqChsSet` — Verify the string-array **aggregate byte size** formula
  `sum(4 + len(utf8))`: does the declared size include each element's 4-byte
  length prefix? One non-destructive live set/get round trip settles all four.
- [ ] `Piezo.HystValsSet` — Four independent count/array pairs. Confirm the X/Y
  and fast/slow pairing is not swapped (the PDF's "Number of fast axis points 2"
  naming is fragile). A wrong pairing passes validation but writes wrong
  hysteresis data.

## Tier 2 — Actively used command with genuinely ambiguous fields

- [ ] `Scan.PropsGet` —
  - (a) "Size of Number of Parameters per Module array" is annotated as the
    element count of an int32 array; it could be a byte size.
  - (b) The `parameters` string matrix: confirm rows/columns are not transposed.
  - If a live script has already called this successfully, both are confirmed;
    check that first.

## Tier 3 — Receive side, never exercised; failures will be loud, check before first use

- [ ] `CPDComp.DataGet` — Highest-risk grouping: `Size 1` is assigned to the
  three *forward* arrays and `Size 2` to the three *backward* arrays. Verify the
  grouping boundary against the PDF; a wrong split misaligns silently when the
  two sizes happen to be equal.
- [ ] Oscilloscope/analyzer family — all annotate a "Data ... size" field as the
  element count of a float array. Reference implementations agree it is a count;
  one live oscilloscope grab confirms the whole family:
  - [ ] `Osci1T.DataGet`
  - [ ] `Osci2T.DataGet`
  - [ ] `OsciHR.OsciDataGet`
  - [ ] `OsciHR.PSDDataGet`
  - [ ] `PLLSignalAnlzr.OsciDataGet`
  - [ ] `PLLSignalAnlzr.FFTDataGet`
  - [ ] `PLLZoomFFT.DataGet`
  - [ ] `SpectrumAnlzr.DataGet`
- [ ] `DigLines.TTLValGet` — "TTL voltages size" on a uint32 array: count or
  bytes (4x difference).
- [ ] `Piezo.HystValsGet` — Same pairing question as `Piezo.HystValsSet`.
- [ ] Matrix responses never used — verify rows/columns order once for the
  family; all follow the same "Data rows / Data columns" pattern, so one
  confirmation with a non-square sweep (e.g. `GenSwp.Start`) likely covers all:
  - [ ] `File.datLoad` (both the `data` matrix and the string `header` matrix)
  - [ ] `Script.DataGet`
  - [ ] `TipRec.DataGet`
  - [ ] `BiasSwp.Start`
  - [ ] `GenSwp.Start`
  - [ ] `LockInFreqSwp.Start`
  - [ ] `PLLFreqSwp.Start`
  - [ ] `PLLPhasSwp.Start`
- [ ] Dual-count string-array getters — confirm which count belongs to which
  array where the field names are near-duplicates:
  - [ ] `GenSwp.AcqChsGet` (`num_channels` vs `num_channels_2`)
  - [ ] `HSSwp.AcqChsGet` (three counts)
  - [ ] `HSSwp.SwpChSigListGet`
  - [ ] `PICtrl.CtrlChGet`
  - [ ] `PICtrl.InputChGet`

## Low risk — validated by prior hardware use, skim only

These ran with identical size semantics under the old heuristic on the real
setup:

- `Signals.ValsGet` (both sides)
- `Scan.FrameDataGrab`
- `Scan.BufferGet` / `Scan.BufferSet`
- `BiasSpectr.Start` / `ZSpectr.Start` (data matrix and parameters array)
- `BiasSpectr.ChsGet` / `BiasSpectr.PropsGet`
- `ZSpectr.ChsGet` / `ZSpectr.PropsGet`
- `Signals.NamesGet`
- `Marks.PointsGet` (covered by a binary regression fixture)

## Separate from protocol semantics — a code bug to fix

- [ ] `HSSwp.Start` — Its send field sanitizes to `timeout`, which collides with
  `send_fields()`'s own `timeout=` keyword, making that protocol field
  unreachable through the named API. Needs a code change (e.g. rename the control
  parameters to `_timeout` / `_check_error`), not a manual protocol check. Add a
  lint so a future PDF revision cannot silently reintroduce a collision.
