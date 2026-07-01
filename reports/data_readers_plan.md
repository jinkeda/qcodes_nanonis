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
class SxmChannel:              # one .sxm channel
    name: str; unit: str
    directions: tuple[str, ...]        # which of ("forward","backward") this channel stores
    forward: np.ndarray | None         # 2-D; None if not stored in that direction
    backward: np.ndarray | None
    # NB: the header DATA_INFO table declares direction per channel as
    # "both" | "fwd" | "bwd"; that governs the binary stride (a "both" channel
    # occupies two frames, a single-direction channel one). The model represents
    # availability explicitly rather than assuming every channel has both.

@dataclass(frozen=True)
class SxmData:                 # .sxm — one scan frame, N channels
    channels: tuple[SxmChannel, ...]
    region: FrameGeometry              # center_x/y, width, height, angle (SI)
    pixels: int; lines: int
    scan_direction: str                # raw header ":SCAN_DIR:" "up"/"down" — NOT reinterpreted
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
- **Real fixtures already exist** in [`data_example/`](../data_example/) — use
  them, don't wait on hardware:
  - `FGT_0030.sxm` — 256×256, 4 channels (`Current (A);Z (m);LI Demod 1 X (A);LI
    Demod 1 Y (A)`), `:SCAN_DIR: down`, `:SCAN_ANGLE: 90`, `SCANIT_TYPE FLOAT
    MSBFIRST`, `:SCANIT_END:`-delimited ASCII header then big-endian float data.
  - `Grid Spectroscopy023.3ds` — 64×64 grid, `Points=101`, sweep `Bias (V)`,
    6 channels, `Fixed parameters`/`Experiment parameters`, `:HEADER_END:` then
    binary records.
  - `Bias-Spectroscopy_00146.dat` — tab-separated header (`key\tvalue\t`) +
    `[DATA]` table; 4 sweeps, 201 points, 6 channels.
  These serve as the **regression oracle** (assert reads match nanonispy_kj's raw
  read). The **paired orientation ground-truth** fixture is separate: the `.sxm`
  saved by [`scan_gate_plan.md`](scan_gate_plan.md) **G-3** *with* its in-memory
  `ScanResult` (see Testing strategy for why both are needed).
- **Acceptance:** the extraction lands green (166 tests) with no sideways or
  duplicated types; models + validation compile and type-check; the three
  `data_example/` files are wired as committed fixtures; nanonispy_kj imports and
  reads each at the raw level in a smoke test.

### D1 — `.sxm` reader (`data/readers/sxm.py`)  ← ground-truth validated
- Parse via nanonispy_kj → `SxmData`; convert units to SI; retain the raw header,
  raw array order, and the header scan direction (`:SCAN_DIR:` — `up`/`down`; the
  `FGT_0030.sxm` fixture is `down`).
- **Decode the `DATA_INFO` per-channel direction (`both`/`fwd`/`bwd`).** A channel's
  direction field governs the binary stride — a `both` channel occupies two frames
  (forward then backward), a single-direction channel one — so the model must carry
  which directions each channel actually has (see `SxmChannel`), not assume both.
  `spaik`'s `SXM.get_channel` ([SXM.py:150-164](../../spaik/src/spaik/Utilities/SXM.py#L150-L164))
  is the reference for this stride logic; nanonispy_kj likely handles the bytes, but
  our model must represent availability.
- **Develop + regression-test against `FGT_0030.sxm`** first (no hardware needed):
  values match nanonispy_kj's raw read, 4 channels present, geometry parsed from
  `:SCAN_RANGE:`/`:SCAN_OFFSET:`/`:SCAN_ANGLE:`.
- **Orientation — start from the confirmed `spaik` convention.** `spaik`'s
  `SXM.get_channel` ([SXM.py:179-186](../../spaik/src/spaik/Utilities/SXM.py#L179-L186))
  encodes a battle-tested `.sxm` **file** convention: `SCAN_DIR == "up"` → flip rows
  (axis 0), and `backward` → flip columns (axis 1). This is not a guess — it agrees
  with our own live characterization (the scan-gate row result: physically-indexed
  buffer, `up`/`down` fill opposite ends), and `backward = fliplr(forward)` is
  exactly the physically-indexed fast-axis that scan-gate **G-2** is confirming.
  Treat it as the **expected** row/column order for the file reader.
- **Cross-check it against ground truth (don't just trust it):** still read the G-3
  fixture and confirm the file's row/column layout against the in-memory `ScanResult`
  from the same acquisition — because `spaik`'s flips are the *file* convention and
  the live `FrameDataGrab` buffer is a separate artifact (the
  `verify_row_orientation.py` docstring warns the file may carry its own
  header-driven orientation). Expected outcome: they agree with `spaik`; if they
  don't, the paired `ScanResult` wins and we record the discrepancy. Store the file's
  orientation as an independent fact; the xarray/QCoDeS adapters apply it.
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

### D5 — Optional session-config reader (`data/readers/session.py`) — low priority

**Decoupled from the file readers; never auto-loaded.** The measurement files are
self-describing — each header already carries the config relevant to *that*
measurement (piezo calibration, Z-controller, bias, gains, scanfield, channels). So
the core readers do **not** read `Nanonis-Session.ini` (see Non-goals for why).

`Nanonis-Session.ini` ([`data_example/`](../data_example/), ~37 sections) is a
different artifact: a **global controller/GUI configuration snapshot** holding
module state the file headers do *not* carry — full `LockInADV`, `Atom Tracking`,
`OscillationControl`, per-`Input`/`Output`, `Bias Spectroscopy` defaults, plus GUI
state (`WindowPositions`, `Charts`) that is irrelevant to analysis.

- Parse with stdlib `configparser` (no nanonispy_kj) → a typed `SessionConfig`
  exposing the measurement-relevant sections; keep the raw sections available.
- **Consume explicitly, never implicitly:** a caller that wants to enrich a
  `SxmData`/`DatData` with session context combines them at the analysis layer.
  A reader result never depends on a sibling `.ini`.
- **Acceptance:** `Nanonis-Session.ini` parses into `SessionConfig`; the module
  sections a caller is likely to want (lock-in, atom-tracking, bias-spec defaults)
  are typed; no file reader imports it.

> **Staleness caveat (why it's not provenance):** the `.ini` is one file per
> session, overwritten as settings change — *not* versioned per measurement. For an
> old file the current `.ini` may not reflect acquisition-time state; the file's own
> frozen header is authoritative and wins on any disagreement.

### D6 — Independent transforms layer (`data/transforms.py`) — separate from readers

**Explicitly decoupled: a reader never applies a correction.** Readers return raw
domain data (raw array order, raw values); background-flattening is a *separate,
opt-in* layer a caller invokes on already-read domain data. This is the same
principle as "no silent flipping on read" — `spaik` couples correction into
`SXM.get_channel` (`correction=` argument), which is exactly the mixing this plan
rejects. Keeping transforms independent means a reader result is always the
unmodified file, and any flattening is an explicit, recorded downstream step.

Rebuild `spaik`'s proven correction catalogue
([SXM.preprocessSXM](../../spaik/src/spaik/Utilities/SXM.py#L206-L304)) as clean,
pure, typed functions — **adopt the recipes, not the code**:

- `subtract_average` / `subtract_vaverage` — per-row / per-column mean removal;
- `subtract_line` / `subtract_vline` — per-row / per-column linear-fit removal;
- `subtract_plane` — global best-fit-plane removal.

Requirements that make this *better* than `spaik`'s version:

- **NaN-safe.** `spaik` `assert`s no NaN and crashes on a partial/aborted scan;
  these must honor `NaNPolicy` and operate on finite values (e.g. `nanmean`,
  masked fits) so a partially-scanned `SxmData` is still flattenable.
- **Pure and typed.** `array -> array` (or `SxmChannel -> SxmChannel`), no I/O, no
  hidden display coupling; each returns a new value (immutable in, immutable out).
- **Provenance-friendly.** A caller records which transform was applied; the raw
  data remains available on the domain model.

**Dependency note:** `data/transforms.py` is a leaf like the readers (numpy +
`nanonis.types` for `NaNPolicy` only); it imports **no** reader and no reader
imports it. Priority: after D1 (needs `SxmData`), independent of D2–D5.

- **Acceptance:** each transform matches `spaik`'s output on a finite fixture
  (regression oracle), leaves NaN handling to `NaNPolicy` on a partial frame, and
  no reader calls it.

## Testing strategy (no simulator; fixtures are the oracle)

Mirrors the two-tier idea, adapted to a hardware-free vertical:

1. **Fixture + oracle tests (CI):** parse the committed `data_example/` files;
   assert values against nanonispy_kj's raw read (the regression oracle) and
   against declared shapes. Pure, offline, deterministic. This covers *correctness
   of the parse* but **not orientation** — an existing file has no paired ground
   truth, so which physical edge its matrix row 0 / column 0 represents cannot be
   proven from the file alone.
2. **Ground-truth cross-check (authoritative, via the scan gate):** a `.sxm` saved
   by scan gate G-3 is read and validated against the in-memory `ScanResult` from
   the *same* acquisition — the analogue of "live-hardware validation" for a
   reader, and the **only** check that pins the file's orientation. This is why
   both oracles exist: `data_example/` proves the bytes decode correctly; the
   paired G-3 file proves what they *mean* geometrically.

Plus unit tests for validation (short/truncated files, non-unique names, NaN
policy) and adapter orientation logic (pure, synthetic arrays).

**Generating fixtures on demand — through existing workflows, not `data/`.** The
`data_example/` files are a fixed snapshot; when a milestone needs a configuration
they don't cover (a backward-sweep `.dat`, a forward-only vs bidirectional `.sxm`,
a particular channel set or resolution), acquire one by driving the **existing,
safety-gated** workflows on the controller — `BiasSpectroscopyWorkflow` → `.dat`,
`ScanWorkflow(autosave=…)` → `.sxm` — which also return the in-memory domain
result, so you get a **paired oracle** (bytes *and* geometric meaning), the G-3
handoff generalized. This is a developer/test-authoring step through workflows
that enforce preflight/approval; it does **not** make `data/` control hardware, and
scan-based generation requires the approved rig policy (scan gate G-1). **Gap:**
there is no grid-spectroscopy workflow yet, so a `.3ds` variant with a specific
configuration must be produced from the Nanonis GUI by an operator, not from our
code.

## Open questions (resolve in D0)

1. **nanonispy_kj: vendor or depend?** Package-depend (pin git+commit) is
   proposed; vendoring is the fallback if the installed rig needs a patched
   variant. Confirm it reads the controller's actual `.sxm`/`.3ds`/`.dat` versions.
2. **`.dat` variants.** The fixture `Bias-Spectroscopy_00146.dat` is a
   multi-sweep bias spectroscopy file (`Number of sweeps 4`, tab-separated
   `key\tvalue` header, `[DATA]` table). Enumerate the *other* `.dat` flavors this
   rig emits (single spectrum, history/time trace) so D3 covers them, not just this
   one.
3. **`.sxm` header direction field.** Confirmed from the fixture: the key is
   `:SCAN_DIR:` with value `up`/`down` (`FGT_0030.sxm` = `down`). Remaining: map it
   onto the shared `RowOrder`/`ColumnOrder` (now in `nanonis.geometry`) — which
   requires the paired G-3 ground truth (an existing file's `:SCAN_DIR:` labels the
   *scan* direction, not which matrix edge is row 0).

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
- **The core file readers do not read `Nanonis-Session.ini`.** Files are
  self-describing; the `.ini` is unversioned global GUI/module state that can drift
  from acquisition-time settings, so coupling a reader to it would break the
  one-file→one-object contract and reproducibility. Session config is a *separate,
  optional* reader (D5), consumed explicitly at the analysis layer only.
- **The core file readers do not apply background corrections.** A reader returns
  the raw file, never a flattened array. Corrections live in an independent,
  opt-in `data/transforms.py` (D6) that operates on already-read domain data —
  deliberately *not* a `correction=` argument on the reader (the coupling `spaik`
  has and this plan rejects).
- QCoDeS persistence stays **optional/dormant** (consistent with the platform's
  current stance) — D4 builds the adapter but nothing in the readers depends on it.

## References

- [`blueprint.md`](blueprint.md) — Target architecture (`data/` box) and vertical
  backlog item 1.
- [`data_example/`](../data_example/) — real regression fixtures: `FGT_0030.sxm`,
  `Grid Spectroscopy023.3ds`, `Bias-Spectroscopy_00146.dat`, and
  `Nanonis-Session.ini` (the D5 session-config input).
- [`scan_gate_plan.md`](scan_gate_plan.md) — G-3 produces the paired `.sxm` +
  `ScanResult` orientation ground truth.
- [`nanonispy_kj`](https://github.com/jinkeda/nanonispy_kj) — the reused byte-layer
  parser.
- `spaik` recipe catalogue (compared, not copied):
  [`SXM.py`](../../spaik/src/spaik/Utilities/SXM.py) (`.sxm` orientation +
  `DATA_INFO` stride + correction catalogue),
  [`Nanonis3ds.py`](../../spaik/src/spaik/Utilities/Nanonis3ds.py) (`.3ds` layout),
  [`Tools.py`](../../spaik/src/spaik/Utilities/Tools.py) (git-provenance recipe).
- [`qcodes/scan.py`](../src/nanonis/qcodes/scan.py),
  [`qcodes/spectroscopy.py`](../src/nanonis/qcodes/spectroscopy.py) — the
  acquire-first adapter pattern D4 reuses.
