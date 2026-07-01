# Data Readers Vertical — Implementation Plan

Status: proposed (rev. 1) · Date: 2026-07-01

The next vertical after scan, and the top item of the blueprint's vertical
backlog. It builds the `nanonis.data` package: typed STM **domain data models**
and **Nanonis file readers** (`.sxm`, `.3ds`, `.dat`), plus **read → domain →
optional QCoDeS/xarray** adapters. Unlike every prior vertical, it **touches no
hardware** — so it has no lab-policy or piezo-safety blocker — but it inherits the
same discipline: typed models, validation before use, explicit provenance, and a
real acceptance oracle (here, real files) rather than assumptions.

Meant to be worked **alongside** [`scan_gate_plan.md`](scan_gate_plan.md): that
plan's item **G-3** (a full autosaved `run()`) produces the real `.sxm` file that
**D1** below validates the `.sxm` reader against. That handoff is the whole reason
the two plans share a live session — the reader's orientation must be checked
against ground truth, not assumed equal to the scan buffer's `row_order`.

## Context

[`data/__init__.py`](../src/nanonis/data/__init__.py) is a docstring stub. `spaik`
and the wider group rely on reading `.sxm` (images), `.3ds` (grid spectroscopy),
and `.dat` (point spectroscopy / history) files; the blueprint names
[`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) as the intended
low-level parser to **reuse, not re-derive**. The value this vertical adds over
raw nanonispy is the platform's house style: immutable typed models, I/O-free
validation, `to_metadata()` provenance, and adapters that feed QCoDeS/xarray the
same acquire-first way [`qcodes/scan.py`](../src/nanonis/qcodes/scan.py) and
[`qcodes/spectroscopy.py`](../src/nanonis/qcodes/spectroscopy.py) do.

## Design rules (inherited + vertical-specific)

- **Dependency direction (non-negotiable):** `data/` imports **nothing** from
  `nanonis.command`, `nanonis.protocol`, `nanonis.workflows`, or `nanonis.qcodes`.
  It is a leaf. The **one** downward dependency it *does* take is on the neutral
  bottom-level primitives `nanonis.geometry` / `nanonis.types` (see the next
  section) — shared value types that depend on nothing themselves, so both `data/`
  and `workflows/` can import them without either depending on the other. The
  data→QCoDeS adapter lives under `qcodes/` (consuming domain data), and the
  data→xarray adapter lives under `data/adapters/` (xarray is a data-model
  dependency, not hardware). Readers **must not** control hardware.
- **Reuse nanonispy_kj for the byte layer.** Do not re-implement Nanonis binary
  parsing. Wrap it behind typed domain models (see "Reuse decision" below).
- **Units = SI** (metres, volts, seconds), matching the rest of the platform.
  Convert on read; never surface raw controller units downstream.
- **No pandas, no pickle** in the domain layer. Arrays are `numpy`; tables are
  typed structures, not DataFrames.
- **Typed, immutable, validated** models with `to_metadata()`, mirroring
  `BiasSpectroscopyResult` / `ScanResult`. Validation is I/O-free and runs after
  parse, before the model is handed out.
- **Preserve raw order; interpret separately.** Exactly like `ScanResult`: the
  reader stores the file's array as-is plus the header's declared orientation
  fields, and orientation is *interpreted* by an adapter — never silently flipped
  on read. (This is what makes the D1 cross-check meaningful.)

## Prerequisite — shared neutral primitives (`nanonis.geometry`, `nanonis.types`)

**D0 does not start until this is done.** `data/` and `workflows/` are parallel
leaves that need the *same* value types (frame geometry, orientation literals, a
non-finite policy). The wrong resolutions are (a) importing them from
`workflows` — sideways dependency, violates the direction rule — or (b) cloning
them into `data/` — the "parallel types, drifting conventions" trap (two rotation
conventions, two `NaNPolicy`s). The right resolution is a **bottom-level neutral
module that depends on nothing and that both packages import downward.**

Extract into `nanonis.geometry` / `nanonis.types` (a pure-values layer at the same
level as `protocol`, hardware-free, I/O-free):

| Symbol | Moves from | Neutral because |
| --- | --- | --- |
| `RowOrder`, `ColumnOrder` (Literals) | `workflows/scan/geometry.py` | pure type aliases |
| `scan_coordinate_grids(...)` | `workflows/scan/geometry.py` | pure numpy; takes geometry + orders |
| `FrameGeometry` (center/width/height/angle, `corners()`) | **new**, factored out of `ScanRegion` | pure value + math, no client |
| `NaNPolicy` (`ALLOW`/`WARN`/`RAISE`) | `workflows` | pure enum, no hardware coupling |

**What stays in `workflows`:** `ScanRegion` keeps its `snapshot()` / `apply()` /
`patch()` — those talk to a `CommandClient` (hardware I/O) and must **not** sink
into a neutral module. `ScanRegion` **composes** `FrameGeometry` (holds one /
delegates geometry + `corners()`) rather than being replaced by it, and
`scan_coordinate_grids` takes the neutral `FrameGeometry` instead of a
`ScanRegion`.

**Cost to pay deliberately (not discover mid-D1):** this refactors the
**already-realized** scan vertical — `workflows/scan/*` and
[`qcodes/scan.py`](../src/nanonis/qcodes/scan.py) import the moved symbols, so
their import sites change. It is mechanical, but it must land as one commit with
the **166 tests still green** (they are the regression gate), and it is a
scan-vertical edit — coordinate it with [`scan_gate_plan.md`](scan_gate_plan.md)
so the two don't step on the same files. After it, `data/models.py` reuses
`FrameGeometry`, `data/validation.py` reuses `NaNPolicy`, and the adapters speak
one `RowOrder`/`ColumnOrder` vocabulary across acquired and read frames.

## Reuse decision — nanonispy_kj

**Proposed:** depend on `nanonispy_kj` as the low-level reader (it already parses
the three formats and is validated), and build a thin typed façade on top. Rules:

- nanonispy_kj output (its header dict + raw arrays) is an **implementation
  detail** confined to `data/readers/*.py`. It never leaks past the domain model.
- Each reader returns a platform domain model (`SxmData`, `Grid3DData`,
  `DatData`), not a nanonispy object.
- Pin the dependency (git URL + commit) and record its version in `to_metadata()`
  for provenance.

Decisions to confirm before D0 (see Open questions): vendor vs. package-depend,
and whether nanonispy_kj covers the installed controller's file variants.

## Domain models (`data/models.py`)

Typed, frozen, validated. Sketch (fields firmed up against real files in D0):

```python
@dataclass(frozen=True)
class SxmData:                 # .sxm — one scan frame, N channels
    channels: tuple[SxmChannel, ...]   # each: name, unit, forward+backward 2-D arrays
    region: FrameGeometry              # center_x/y, width, height, angle (SI)
    pixels: int; lines: int
    scan_direction: str                # raw header "up"/"down" — NOT reinterpreted
    header: Mapping[str, str]          # full raw header, retained
    def to_metadata(self) -> dict: ...

@dataclass(frozen=True)
class Grid3DData:              # .3ds — grid spectroscopy
    sweep_signal: SweepAxis            # name, unit, values (1-D)
    channels: tuple[Grid3DChannel, ...]  # each: 3-D cube (lines, pixels, sweep)
    fixed_parameters: Mapping[str, np.ndarray]  # per-pixel 2-D maps
    region: FrameGeometry
    def to_metadata(self) -> dict: ...

@dataclass(frozen=True)
class DatData:                # .dat — point spectroscopy / history
    columns: tuple[DatColumn, ...]     # each: name, unit, 1-D values
    header: Mapping[str, str]
    def to_metadata(self) -> dict: ...
```

`FrameGeometry` is **the one neutral type from `nanonis.geometry`** (see the
prerequisite section), imported by both `data/` and `workflows/`. It is *not* a
parallel `data/`-local copy: a read frame and an acquired frame describe geometry
through the identical type and the identical rotation/`corners()` math, so there
is exactly one convention. `ScanRegion` composes this same `FrameGeometry` and
adds the hardware snapshot/apply on top.

## Validation (`data/validation.py`)

I/O-free checks run after parse, before hand-off: array shapes match declared
`pixels`/`lines`/sweep length; channel/column names unique; units present; finite
handling via the shared `NaNPolicy` (`ALLOW`/`WARN`/`RAISE`) imported from
`nanonis.types` — the *same* enum the workflow layer uses, not a copy — so
partial/aborted files are handled explicitly rather than surfacing silent NaNs.

## Adapters

- **`data/adapters/xarray.py`** — domain model → `xarray.DataArray`/`Dataset` with
  physical coordinate axes. Orientation is applied **here**, from the model's
  stored raw order + declared direction, using the shared `RowOrder`/`ColumnOrder`
  and `scan_coordinate_grids` from `nanonis.geometry` (the same primitives the scan
  adapter uses — one vocabulary, one rotation convention). Optional dependency
  (guard the import).
- **`qcodes/data.py`** (under `qcodes/`, per the dependency rule) — domain model →
  QCoDeS dataset, acquire-first, provenance metadata, reusing the 2-D meshgrid
  setpoint pattern already proven in `qcodes/scan.py`. Sxm frames map cleanly onto
  that pattern; `.3ds` grids add a sweep dimension; `.dat` maps onto the 1-D
  spectroscopy pattern from `qcodes/spectroscopy.py`.

## Milestones

Priority order = frequency of use. `.sxm` first because it is the most common file
and because it is the one the scan gate can validate against ground truth.

### D0 — Neutral primitives, foundations, fixtures, and the reuse decision
- **Extract `nanonis.geometry` / `nanonis.types` first** (the prerequisite
  section): move `RowOrder`/`ColumnOrder`/`scan_coordinate_grids`/`NaNPolicy`,
  factor `FrameGeometry` out of `ScanRegion`, and update `workflows/scan/*` +
  `qcodes/scan.py` import sites — one commit, 166 tests still green.
- Settle the nanonispy_kj reuse decision (Open questions); pin + smoke-test it.
- Define `data/models.py` + `data/validation.py` skeletons on the neutral
  `FrameGeometry` / `NaNPolicy` (no `data/`-local geometry or policy copies).
- Collect **committed test fixtures**: small real `.sxm`/`.3ds`/`.dat` files. The
  authoritative `.sxm` fixture is the one saved by
  [`scan_gate_plan.md`](scan_gate_plan.md) **G-3**, archived with its `ScanResult`.
- **Acceptance:** the extraction lands green (166 tests) with no sideways or
  duplicated types; models + validation compile and type-check; fixtures committed;
  nanonispy_kj imports and reads each fixture at the raw level in a smoke test.

### D1 — `.sxm` reader (`data/readers/sxm.py`)  ← ground-truth validated
- Parse via nanonispy_kj → `SxmData`; convert units to SI; retain raw header,
  raw array order, and the header `scan_direction`.
- **Orientation cross-check (the point of pairing with the scan gate):** read the
  G-3 fixture and confirm whether the **file's** row/column layout matches the
  in-memory `ScanResult` from the same acquisition. Do **not** assume the `.sxm`
  reader's `row_order` equals the scan buffer's `top_to_bottom` — the
  `verify_row_orientation.py` docstring explicitly warns the file may carry its own
  header-driven orientation. Record the file's orientation as an independent fact;
  the xarray/QCoDeS adapters apply it.
- **Acceptance:** every channel/value of the fixture matches nanonispy_kj's raw
  read (regression oracle) and matches the paired `ScanResult` values; the file's
  orientation relative to `ScanResult` is documented; validation catches a
  truncated/short file.

### D2 — `.3ds` grid-spectroscopy reader (`data/readers/three_ds.py`)
- Parse → `Grid3DData` (per-channel 3-D cube + per-pixel fixed-parameter maps +
  sweep axis). Reconcile grid X/Y geometry with `FrameGeometry`.
- **Acceptance:** cube/map/sweep shapes consistent and match the nanonispy_kj
  oracle on a real `.3ds` fixture; sweep axis monotonic/handled; NaN policy honored.

### D3 — `.dat` point-spectroscopy reader (`data/readers/dat.py`)
- Parse → `DatData` (typed columns + header). Handle both single-spectrum and
  multi-column history `.dat` variants present on this rig.
- **Acceptance:** columns/units/values match the oracle on real `.dat` fixtures;
  a bias-spectroscopy `.dat` saved by the live rig round-trips.

### D4 — Adapters
- `data/adapters/xarray.py` and `qcodes/data.py` per "Adapters" above.
- **Acceptance:** an `.sxm` → xarray `DataArray` carries correct physical coords
  (orientation from D1); an `.sxm` → QCoDeS dataset registers with 2-D meshgrid
  setpoints + provenance, reusing the `qcodes/scan.py` pattern; xarray import is
  optional (guarded).

## Testing strategy (no simulator; fixtures are the oracle)

Mirrors the two-tier idea, adapted to a hardware-free vertical:

1. **Fixture + oracle tests (CI):** parse committed real files; assert values
   against nanonispy_kj's raw read (the regression oracle) and against declared
   shapes. Pure, offline, deterministic.
2. **Ground-truth cross-check (authoritative, via the scan gate):** the D1 `.sxm`
   read is validated against the in-memory `ScanResult` from the same live
   acquisition (scan gate G-3) — the analogue of "live-hardware validation" for a
   reader. This is the one check that proves the file bytes mean what we think.

Plus unit tests for validation (short/truncated files, non-unique names, NaN
policy) and adapter orientation logic (pure, synthetic arrays).

## Open questions (resolve in D0)

1. **nanonispy_kj: vendor or depend?** Package-depend (pin git+commit) is
   proposed; vendoring is the fallback if the installed rig needs a patched
   variant. Confirm it reads the controller's actual `.sxm`/`.3ds`/`.dat` versions.
2. **`.dat` variants.** Enumerate which `.dat` flavors this rig emits
   (single spectrum, history, sweep) so D3 covers them, not just one.
3. **`.sxm` header direction field.** Confirm the exact header key/values for scan
   direction and map them onto the shared `RowOrder`/`ColumnOrder` (now settled to
   live in `nanonis.geometry` — see below). Live confirmation folds into scan gate
   G-3's read of the saved file.

> **Resolved (was Q2 + Q4) — `FrameGeometry`/orientation ownership.** Both are
> settled by the "shared neutral primitives" prerequisite: `FrameGeometry`,
> `RowOrder`, `ColumnOrder`, and `scan_coordinate_grids` move to `nanonis.geometry`
> (with `NaNPolicy` in `nanonis.types`), and both `data/` and `workflows/` import
> them. There is **one** geometry type, one rotation convention, and one
> orientation vocabulary — no parallel definitions to drift. This closes the
> reviewer's dependency-rule/reuse contradiction.

## Non-goals

- No hardware control, ever, from `data/`.
- No writing of Nanonis files (read-only vertical for now).
- No pandas/pickle re-introduction.
- QCoDeS persistence stays **optional/dormant** (consistent with the platform's
  current stance) — D4 builds the adapter but nothing in the readers depends on it.

## References

- [`blueprint.md`](blueprint.md) — Target architecture (`data/` box) and vertical
  backlog item 1.
- [`scan_gate_plan.md`](scan_gate_plan.md) — G-3 produces the D1 `.sxm` oracle.
- [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) — the reused byte-layer
  parser.
- [`qcodes/scan.py`](../src/nanonis/qcodes/scan.py),
  [`qcodes/spectroscopy.py`](../src/nanonis/qcodes/spectroscopy.py) — the
  acquire-first adapter pattern D4 reuses.
