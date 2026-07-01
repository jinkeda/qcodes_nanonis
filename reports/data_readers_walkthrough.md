# Data Readers Vertical — Implementation Walkthrough

Implemented: 2026-07-01

## Outcome

The `nanonis.data` vertical now reads `.sxm`, `.3ds`, `.dat`, and optional
`Nanonis-Session.ini` files into immutable typed models. It also provides
I/O-free validation, SI conversion, explicit background transforms, xarray
adapters, and acquire-first QCoDeS persistence. No code under `nanonis.data`
imports or controls hardware.

The original 166-test workflow/command baseline remains green. The completed
suite has 204 passing tests, including oracle comparisons against all three real
files in `data_example/`.

[`examples/data_readers_demo.ipynb`](../examples/data_readers_demo.ipynb) is the
offline, run-from-top tutorial for every reader, visualization, transform,
xarray adapter, and optional QCoDeS persistence path described below.

## D0: shared primitives and parser boundary

`nanonis.geometry` is now the single owner of:

- `FrameGeometry`, including validation and clockwise Nanonis rotation math;
- `RowOrder` and `ColumnOrder`;
- `scan_coordinate_grids`.

`ScanRegion` composes `FrameGeometry` and delegates its geometry fields and
`corners()`. Its existing scalar constructor remains compatible, while
`ScanRegion(FrameGeometry(...))` and `ScanRegion(geometry=...)` are also
supported. The old workflow geometry module is a compatibility re-export.

`NaNPolicy` moved to `nanonis.types`; workflow results and file readers now use
the same enum instance.

The parser is isolated in `data/readers/_parser.py`. It prefers `nanonispy2`
when installed and supports released `nanonispy` as the pinned runtime fallback.
Parser name/version is stored in every model's provenance metadata. Metadata also
records the `qcodes-nanonis` package version, the source git commit when running
from a checkout (or `QCODES_NANONIS_GIT_COMMIT` when injected by a build), and
the controller Nanonis/software versions exposed by the file header.

The proposed fork commit `86d1983dd11eda4d771eac2ad5f90df50f7757bc` was
evaluated but cannot be installed as a PEP 517 dependency: its `pyproject.toml`
names the unavailable backend `setuptools.backends._legacy`. That install failure
is the sufficient disqualifier. Consequently the project pins `nanonispy==1.1.0`
and adds a contained NumPy-2 compatibility context for that release.

> **Correction (per review): the payload stride is not a "mixed-channel" concern.**
> An earlier draft justified the pin partly by claiming a global direction count is
> "incorrect for mixed `both`/`fwd`/`bwd` channels." That case does **not** occur:
> whether backward data is saved is a *global* Nanonis scan setting, so every row of
> `DATA_INFO` shares one `Direction` — a file is uniformly `both` **or** uniformly
> single-direction, never mixed per channel. A single global count is therefore
> correct for every real file. `read_sxm` still keeps a header-only fallback
> (`parse_sxm_header_only` + `_read_directional_payload`) that decodes the stride
> per channel, but its only realistic trigger is a **uniform single-direction**
> file (a scan saved without backward) that the low-level reshape cannot handle —
> not mixed channels.
>
> **Known coverage gap:** the sole `.sxm` fixture (`FGT_0030.sxm`) is uniformly
> `both`, so it parses via the primary path and the fallback is currently
> **unexercised**. Resolve one way or the other: add a uniform single-direction
> fixture if the fallback is load-bearing (nanonispy's reshape fails on it), or
> **remove the fallback as unreachable** if nanonispy already handles
> single-direction files. Do not keep untested defensive code for a case that
> cannot happen.

## D1–D3: file readers and domain models

The public entry points are:

```python
from nanonis.data import read_3ds, read_dat, read_sxm
from nanonis.types import NaNPolicy

scan = read_sxm("frame.sxm", nan_policy=NaNPolicy.WARN)
grid = read_3ds("grid.3ds")
spectrum = read_dat("spectrum.dat", nan_policy=NaNPolicy.ALLOW)
```

The models in `data/models.py` copy arrays to `float64`, mark them read-only,
freeze headers/mappings, validate dimensions and unique names, and expose
JSON-compatible `to_metadata()` provenance.

- `SxmData` contains `SxmChannel` objects with explicit forward/backward
  availability. The reader honors the file's `DATA_INFO.Direction` (uniform across
  channels — see the correction above) instead of assuming two frames per channel,
  so a single-direction file yields one frame per channel. Geometry comes from scan
  range, offset, and angle; the raw `SCAN_DIR` and raw matrix order are retained.
- `Grid3DData` contains a monotonic `SweepAxis`, 3-D channel cubes, all fixed and
  experimental per-pixel parameter maps, and grid geometry.
- `DatData` contains typed 1-D columns. Only the multi-sweep bias-spectroscopy
  variant (`Bias-Spectroscopy_00146.dat`) is supported by the regression-tested
  contract. No support claim is made yet for single-spectrum or history variants;
  each needs a real fixture, especially where normalized column names can collide.

Known prefixes such as pA, nA, mV, nm, ms, kHz, and mT are converted to SI on
read. The real fixtures already use SI for their primary channels, so every scale
factor (including ASCII/Unicode micro forms) is additionally covered by a direct
table-driven unit test.

Models retain their complete immutable parser header for analysis. Normal
`to_metadata()` and QCoDeS persistence use a compact header summary to avoid
duplicating a large header into dataset metadata; callers can explicitly request
the complete JSON-compatible form with `to_metadata(include_header=True)`.

`data/validation.py` counts NaN/Inf values across each model and applies the
shared `ALLOW`, `WARN`, or `RAISE` policy. Structural validation is performed by
the immutable model constructors before any object is returned.

## D4: xarray and QCoDeS adapters

`data/adapters/xarray.py` imports xarray only inside adapter calls. The optional
dependency is exposed as the `xarray` project extra.

For SXM files, orientation is deliberately applied here rather than in the
reader:

- raw `SCAN_DIR == "up"` is flipped on row axis 0;
- backward data is flipped on column axis 1;
- the resulting values use top-to-bottom, left-to-right physical coordinate
  grids from `scan_coordinate_grids`.

`sxm_raw_orders()` and `orient_sxm_array()` make this interpretation directly
testable. `sxm_to_xarray()`, `grid_3ds_to_xarray()`, and `dat_to_xarray()` create
datasets with physical coordinates, units, and provenance.

3DS orientation has no paired ground-truth acquisition. Consequently
`grid_3ds_to_xarray()` requires the caller to provide `row_order`, emits an
unverified-orientation warning, records both declared raw orders in metadata, and
does not flip the cube. This prevents the previous silent `bottom_to_top` default
from being mistaken for a characterized convention.

`qcodes/data.py` implements registration/add pairs for all three domain models:

- SXM uses 2-D row/column meshgrid setpoints, physical X/Y grids, and one
  dependent array per channel/direction;
- 3DS uses broadcast 3-D row/column/sweep setpoints for cubes and 2-D index
  grids for fixed-parameter maps;
- DAT uses a one-dimensional sample-index setpoint.

All adapters consume completed domain data and only persist it; none initiates
acquisition.

## D5: explicit session reader

`read_session()` uses `configparser` and returns `SessionConfig`. Every raw
section remains available through immutable `SessionModule` objects, with
booleans and numeric values typed where possible. Convenience properties expose
the lock-in, atom-tracking, and bias-spectroscopy sections. Measurement readers
never load or depend on a sibling session file.

## D6: independent transforms

`data/transforms.py` provides:

- `subtract_average` and `subtract_vaverage`;
- `subtract_line` and `subtract_vline`;
- `subtract_plane`;
- named dispatch through `apply_transform`.

These functions are pure `array -> new array` operations. Fits use finite values
only, preserve non-finite input locations, and honor `NaNPolicy`. No reader calls
a transform, so raw file data remains unchanged and correction provenance can be
recorded by the caller.

## Verification

Commands run from the project root:

```text
pytest -q
204 passed

ruff check src tests/data
All checks passed!

mypy --follow-imports=skip --ignore-missing-imports \
  src/nanonis/data src/nanonis/geometry.py src/nanonis/types.py \
  src/nanonis/qcodes/data.py
Success: no issues found in 16 source files
```

The tests cover:

- exact SXM channel frames versus nanonispy for `FGT_0030.sxm`;
- exact 3DS cube/sweep values versus nanonispy for
  `Grid Spectroscopy023.3ds`;
- exact DAT columns versus nanonispy for `Bias-Spectroscopy_00146.dat`;
- every supported SI-prefix conversion and representative label/unit parsing;
- truncated SXM rejection, immutable models, shape/name validation, and all
  non-finite policies;
- compact/full metadata behavior plus parser, software/git, and controller
  provenance;
- the SXM up/backward orientation convention, physical xarray grids, and explicit
  unverified 3DS orientation declaration;
- finite and partial/NaN transform behavior;
- session configuration parsing and QCoDeS registration/add behavior.

## Remaining external acceptance check

The scan-gate plan's G-3 checkbox is still open and this repository does not
contain a paired autosaved SXM plus its in-memory `ScanResult`. Therefore the
adapter convention is implemented from the confirmed spaik/file convention and
covered by deterministic synthetic tests, but the final same-acquisition
file-versus-buffer orientation comparison could not be executed. Once G-3
produces that pair, compare each channel/direction after `orient_sxm_array()`;
the paired `ScanResult` remains authoritative if the live controller differs.
