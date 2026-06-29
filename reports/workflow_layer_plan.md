# Workflow Layer — Implementation Plan

Status: proposed (rev. 4) · Date: 2026-06-29

Rev. 4 folds in a fourth review round. Key additions: timeout recovery must
**Stop-and-wait** (the sweep may still run after the client times out);
reconnect must happen **inside** the context-manager bodies; the dual Z-offset
(`PropsSet` vs `TimingSet`) is kept explicit; the QCoDeS adapter splits into
`register()` / `add_result()` phases; M1 splits into M1A (tip state, independent)
and M1B (settings, needs M0A); plus schema regression tests for the corrected
`PropsGet`. `PropsSet` now exists in the config. See the
[Review changelog](#review-changelog).

Rev. 3 corrected: runtime response keys are **snake_case** (rev. 2 was wrong);
`BiasSpectr.PropsGet` was **mis-defined**; long acquisitions need per-command
timeout + socket recovery; config is **snapshot-and-patch**; restoration is
ordered + best-effort.

## Context

`qcodes_nanonis` has a clean 3-layer stack (`protocol` → `command` → `qcodes`)
but **no measurement orchestration**. The QCoDeS channels (`bias.py`, `scan.py`)
are thin parameter getters/setters; nothing runs a measurement end-to-end
(configure module → acquire → normalize → restore state on failure).

`spaik` proves the layer is needed: `SPMMeasurement` is a ~7,000-line god-object
mixing hardware control, pandas configs, pickle I/O, devices, and plotting, with
state restoration in an unprotected `finally`. This plan rebuilds that
functionality properly while matching the repo's layered, Protocol-driven style.

## Design rules (non-negotiable)

- **Dependency direction:** `workflows → CommandClient (Protocol)`. The workflow
  package imports nothing from `nanonis.qcodes` and nothing from `qcodes`.
- **`NanonisController` already is the command client.** `CommandClient` is a
  `Protocol` it satisfies structurally — do not build a parallel client.
- **Units = volts / SI**, matching `configs/commands` (not `spaik`'s mV).
- **No pandas, no pickle** in this layer.

## File layout

```text
src/nanonis/workflows/
├── __init__.py
├── protocols.py          # CommandClient, RecoverableCommandClient
├── errors.py             # WorkflowError, StateRestorationError, SpectroscopyResponseError
├── state.py              # preserve_tip_state(), preserve_bias_spectroscopy_settings()
├── models.py             # BiasSpectroscopyConfig, BiasSpectroscopySettings, SweepAxis
├── result.py             # BiasSpectroscopyResult + normalization (lossless)
└── bias_spectroscopy.py  # BiasSpectroscopyWorkflow (first vertical)
src/nanonis/qcodes/
└── spectroscopy.py       # register_bias_spectroscopy() + add_bias_spectroscopy_result()  (M3)
tests/workflows/
├── conftest.py           # FakeController / RecoverableFakeController
├── test_state.py
├── test_result.py
├── test_schema.py        # PropsGet runtime names + binary trailer fixture; PropsSet field count
└── test_bias_spectroscopy.py
```

## 1. `protocols.py`

```python
@runtime_checkable
class CommandClient(Protocol):
    def send(self, command: str, *args: Any, timeout: float | None = None) -> Any: ...

@runtime_checkable
class RecoverableCommandClient(CommandClient, Protocol):
    def reconnect(self) -> None: ...
```

`NanonisController` satisfies both once §1b lands. `timeout` is added so a single
long acquisition can exceed the default socket timeout without changing it
globally.

### 1b. Controller changes (prerequisite for long acquisitions)

The controller currently has **one fixed 10 s socket timeout** and `send()` has
no per-call override. A real bias spectroscopy easily exceeds 10 s. Required:

- `send(..., timeout: float | None = None)` — temporarily apply the per-command
  timeout on the TCP client, restore the previous value in a `finally`.
- **Lock the whole transaction.** Temporarily mutating the socket timeout (and
  the request→response exchange itself) is unsafe if a controller is shared
  across threads (e.g. a background monitor plus a sweep). Hold an `_io_lock`
  across header/body send, full response receive, and timeout restoration. This
  also prevents interleaved Nanonis responses. (Defensive — only matters under
  concurrent access, but cheap.)

  ```python
  with self._io_lock:
      previous = sock.gettimeout()
      try:
          sock.settimeout(command_timeout)
          ...                      # send + receive complete response
      finally:
          sock.settimeout(previous)
  ```

- **Recovery contract = invalidate → reconnect → Stop-and-wait → restore.** If
  `BiasSpectr.Start` times out or is interrupted, two things are true at once:
  its response may still be in the socket, **and the sweep may still be running
  on the instrument**. Reconnecting clears the stale socket but does *not* stop
  the sweep, so restoration writes could collide with an active acquisition.
  Required sequence:

  ```text
  Start timeout / interrupt
        ↓ disconnect + mark connection unusable
        ↓ reconnect
        ↓ BiasSpectr.Stop
        ↓ poll BiasSpectr.StatusGet (bounded) until not running
        ↓ verify stopped  ── on failure → report state UNKNOWN, do NOT write
        ↓ restore spectroscopy settings
        ↓ restore tip state
  ```

  Track usability state on the controller (e.g. `is_usable`) so restoration can
  refuse to write on a connection that never recovered, rather than each
  workflow re-implementing recovery. This makes `Stop` and `StatusGet`
  **blocking M0B requirements**, not general command-coverage nice-to-haves.

## 2. `state.py` — transactional restoration (build & test first)

Two **separate** scoped context managers, not one god-object snapshot:

- `preserve_tip_state(client)` — bias, setpoint, feedback.
- `preserve_bias_spectroscopy_settings(client)` — the module settings (§3b),
  restored after the run.

Nest them:

```python
with preserve_tip_state(client):
    with preserve_bias_spectroscopy_settings(client):
        ...
```

Requirements (revised from review):

- **Restore on every exit** — normal, Nanonis error, timeout, `KeyboardInterrupt`
  (`try/finally`, covering `BaseException`).
- **Ordered restoration**, based on lab procedure, not field order:
  1. disable feedback if it must be off to change bias safely,
  2. restore bias toward the initial value (see ramp note),
  3. restore current setpoint,
  4. re-enable feedback **last**.
- **Best-effort**: do not stop at the first failed field. Attempt every
  remaining safe operation and collect all failures:

  ```python
  raise StateRestorationError(
      original_error=body_error,
      failures={"bias": ..., "setpoint": ..., "feedback": ..., "settings": ...},
  )
  ```

- **Module-settings restoration also has an order** (tip state is not the only
  thing with ordering): ensure spectroscopy stopped → restore channels → limits
  → timing → properties → **advanced properties last** (Z-controller hold / reset
  bias affect safety). Exact order confirmed on the simulator in M0C.
- After a `Start` timeout/interrupt, restoration runs **only after** a successful
  `reconnect()` **and** confirmed-stopped (§1b); a failed reconnect or unverified
  stop is an explicit restoration failure — report state UNKNOWN, do not write.
- Never `assert` for hardware safety. Log every state change at INFO.

**Reconnect/Stop happens inside the body, not in the restoration `finally`.** The
context managers begin restoring the moment an exception propagates through them,
so recovery must run *before* that — in the innermost workflow body:

```python
with preserve_tip_state(client):
    with preserve_bias_spectroscopy_settings(client):
        try:
            response = client.send("BiasSpectr.Start", 1, config.save_base_name,
                                   timeout=config.acquisition_timeout)
        except (NanonisTimeoutError, KeyboardInterrupt):
            client.reconnect()
            client.send("BiasSpectr.Stop")
            wait_until_spectroscopy_stopped(client)   # bounded StatusGet poll
            raise                                     # now restoration runs on a sane link
```

If `reconnect()` fails, the controller's `is_usable` flag tells the context
managers restoration cannot safely proceed — they skip writes and raise.

> **Ramp note (open).** "Restore bias with a controlled ramp" is the safe ideal,
> but there is **no native Nanonis bias-ramp command** in the registry — only the
> instantaneous `Bias.Set`. `spaik` ramps externally (ADwin) or via stepped
> writes. So the ramp mechanism must be chosen explicitly (stepped `Bias.Set`
> loop with a max step, or a `FolMe`/other primitive) — do not promise "ramp" as
> if it exists. A direct `Bias.Set(initial)` may be acceptable since the initial
> value was already a safe operating point; the risk is only the size of the
> jump from the sweep's end voltage.

> The `spaik` failure mode is that a restore exception in `finally` **masks**
> (not silently swallows) the original acquisition error — `StateRestorationError`
> carrying both is the fix.

## 3. `models.py` — snapshot-and-patch config

The module's real setters need many arguments (`TimingSet` takes 8, `PropsSet`
takes 7). Exposing a few fields with `0.0` defaults would **overwrite valid
existing settings with unsafe zeros**. So config fields are **optional overrides**
(`None` = leave as-is); the workflow reads the full current settings, patches the
non-`None` fields, and sends complete setter argument lists.

```python
@dataclass(frozen=True)
class BiasSpectroscopyConfig:
    start_voltage: float          # V
    stop_voltage: float           # V
    points: int
    channel_indexes: tuple[int, ...]

    sweeps: int = 1
    include_backward: bool = False      # backward-only is NOT supported
    save_individual_sweeps: bool = False

    # NOTE: two distinct Z-offset fields exist on the wire — PropsSet has one and
    # TimingSet has another. spaik sets BOTH, so keep them separate; do not send
    # one value to both setters until M0C proves they mirror each other.
    props_z_offset: float | None = None     # m, -> PropsSet
    timing_z_offset: float | None = None    # m, -> TimingSet
    integration_time: float | None = None   # s
    settling_time: float | None = None       # s
    maximum_slew_rate: float | None = None   # V/s

    save_base_name: str = ""
    acquisition_timeout: float | None = None  # s, per-command override for Start
    restore_tip_state: bool = True
    restore_module_settings: bool = True

    def __post_init__(self):
        # Structural validation only (no I/O). Hardware preflight (Bias.RangeGet)
        # is separate because it needs a live connection.
        if self.points < 2:
            raise ValueError("points must be >= 2")
        if self.sweeps < 1:
            raise ValueError("sweeps must be >= 1")
        if not self.channel_indexes:
            raise ValueError("need >= 1 channel")
        if len(set(self.channel_indexes)) != len(self.channel_indexes):
            raise ValueError("duplicate channel indexes")
        if any(not 0 <= i <= 127 for i in self.channel_indexes):  # verify max vs Signals
            raise ValueError("channel index out of range 0..127")
        if not (np.isfinite(self.start_voltage) and np.isfinite(self.stop_voltage)):
            raise ValueError("non-finite voltage")
        if self.start_voltage == self.stop_voltage:
            raise ValueError("start_voltage == stop_voltage")
        for t in (self.integration_time, self.settling_time):
            if t is not None and t <= 0:
                raise ValueError("times must be > 0 when provided")
```

Invalid config raises **before any command is sent** (test asserts zero sends).

### 3b. `BiasSpectroscopySettings` — typed module snapshot

Separate from tip state. Read via `PropsGet`/`TimingGet`/`AdvPropsGet`/
`LimitsGet`/`ChsGet`, patched, restored after the run:

```python
@dataclass(frozen=True)
class BiasSpectroscopySettings:
    channels: tuple[int, ...]
    save_all: bool
    sweeps: int
    include_backward: bool
    points: int
    props_z_offset: float                # from PropsGet  (distinct from timing.z_offset)
    autosave: bool
    show_save_dialog: bool
    timing: "BiasSpectroscopyTiming"     # 8 fields (see TimingGet), incl. its own z_offset
    advanced: "BiasSpectroscopyAdvanced"
    limits: tuple[float, float]
```

The tristate wire value for backward (and other checkbox setters) is
`1 = enabled, 2 = disabled, 0 = no change`.

> **Dual Z-offset (open, M0C).** `PropsGet`/`PropsSet` expose `z_offset_m` *and*
> `TimingGet`/`TimingSet` expose a Z-offset. `spaik` sets both. They may be the
> same value mirrored by the API, two independent values, or a version quirk —
> unresolved until characterization. Until then, carry both explicitly and never
> collapse them.

## 3c. `result.py` — **lossless** normalized result

Keep the raw channel-major matrix plus ordered names; dict-style access is an
explicit convenience, not the storage form (a `dict[str, list]` overwrites
duplicate channel names and drops order/dimensions).

**Orientation is channel-major** (rows = channels, columns = samples), confirmed
by `spaik` building `pd.DataFrame(matrix.T, columns=channel_names)`
([`BlueNanonisTCP.py:654`](../../spaik/src/spaik/Devices/SPMControllers/BlueNanonisTCP.py)).
So `len(channel_names) == data_rows` is a justified invariant.

```python
FloatArray = npt.NDArray[np.float64]

@dataclass(frozen=True)
class SpectroscopyTrace:
    name: str
    occurrence: int                 # disambiguates duplicate names
    values: FloatArray
    @property
    def unique_name(self) -> str:
        return self.name if self.occurrence == 0 else f"{self.name}#{self.occurrence + 1}"

@dataclass(frozen=True)
class SpectroscopyParameter:
    name: str | None                # None when names unavailable (PropsGet bug / version)
    value: float

@dataclass(frozen=True)
class BiasSpectroscopyResult:
    channel_names: tuple[str, ...]
    data: FloatArray                # channel-major (data_rows, data_columns), read-only owned copy
    data_rows: int
    data_columns: int
    parameters: tuple[SpectroscopyParameter, ...]
    requested_points: int
    requested_sweeps: int
    include_backward: bool
    saved_file: str | None = None

    def __post_init__(self):
        if self.data.shape != (self.data_rows, self.data_columns):
            raise ValueError("matrix shape != declared (rows, columns)")
        if len(self.channel_names) != self.data_rows:
            raise ValueError("channel-name count != data rows (orientation)")

    def traces(self) -> tuple[SpectroscopyTrace, ...]:
        seen, out = {}, []
        for name, values in zip(self.channel_names, self.data):
            occ = seen.get(name, 0); seen[name] = occ + 1
            out.append(SpectroscopyTrace(name, occ, values))
        return tuple(out)

    @property
    def points_match_request(self) -> bool:    # DIAGNOSTIC only, not a requirement
        return self.data_columns == self.requested_points
```

`find_channels` / `get_unique_channel` / `__iter__` are deferred to the first
real consumer.

**Immutability — own the array.** A frozen dataclass does **not** freeze its
NumPy arrays, and `np.asarray` may return a *view* of the caller's buffer, so
`setflags(write=False)` could freeze someone else's array. Always copy:

```python
data = np.array(response["data"], dtype=np.float64, copy=True)
data.setflags(write=False)
```

**Traces are read-only views, not copies.** Once the base matrix is owned and
read-only, `SpectroscopyTrace.values = self.data[index]` is a view that is itself
read-only — no need to copy each channel (avoids N copies). Reconstructed sweep
axes are owned separately (they aren't slices of `data`) and frozen the same way.
Enforce ownership at the boundary: make `normalize_*` the only public constructor,
**or** copy/freeze inside `__post_init__`, so direct construction can't smuggle in
a writable array.

### Sweep axis = reconstructed setpoint, not measured bias

```python
@dataclass(frozen=True)
class SweepAxis:
    values: FloatArray
    unit: str = "V"
    source: str = "configured sweep limits"   # never "measured"
    direction: str = "forward"                 # or "backward"
```

Forward = `np.linspace(start, stop, points)` (owned, read-only); backward =
forward reversed. Keep separate from any measured `Bias (V)` channel that may or
may not be present. Backward-axis reconstruction is a hypothesis until M0C.

### NaN policy (explicit)

```python
class NaNPolicy(Enum):
    ALLOW = "allow"; WARN = "warn"; RAISE = "raise"
```

Default **WARN** (preserve acquired data; a mid-sweep safety abort legitimately
yields NaNs — RAISE would discard real data). **Normalize first, then apply the
policy**, and even `RAISE` must not throw the data away — it raises an error that
*carries the partial result*:

```python
class NonFiniteSpectroscopyDataError(WorkflowError):
    def __init__(self, result, diagnostics):
        self.result = result          # the fully-normalized, inspectable result
        self.diagnostics = diagnostics
        super().__init__(...)
# diagnostics: {"nan_count", "inf_count", "fully_nan_channels": [...], "affected_channels": [...]}
```

Distinguish *any* NaN, *entire-channel* NaN, and non-finite (`±inf`). Ported from
`spaik`'s `NaNinDataError` but as a configurable policy that never loses data.

## 4. `bias_spectroscopy.py` — first vertical

```python
class BiasSpectroscopyWorkflow:
    def __init__(self, client: CommandClient):
        self._client = client

    def run(self, config: BiasSpectroscopyConfig) -> BiasSpectroscopyResult:
        ...
```

No `capture` parameter — tests inspect the returned result directly; QCoDeS
persistence is a caller-side helper (§5). Flow:

The **context manager snapshots on entry** — the workflow does not re-snapshot.
`Open` happens before entering the settings scope, since some getters may require
the module open:

```python
# 1. structural validation already happened at config construction
with preserve_tip_state(client):                       # snapshots tip state on entry
    client.send("BiasSpectr.Open")
    with preserve_bias_spectroscopy_settings(client) as original:   # snapshots settings on entry
        effective = original.patch(config)             # non-None overrides only
        effective.apply(client)                        # ChsSet→PropsSet→LimitsSet→TimingSet→AdvPropsSet
        effective = read_back_effective(client)        # tristate 0 = no change → readback authoritative
        try:
            response = client.send("BiasSpectr.Start", 1, config.save_base_name,
                                   timeout=config.acquisition_timeout)
        except (NanonisTimeoutError, KeyboardInterrupt):
            client.reconnect(); client.send("BiasSpectr.Stop")
            wait_until_spectroscopy_stopped(client); raise
        result = normalize_bias_spectroscopy_response(response, props=effective_props,
                     requested_points=effective.points, ...)   # NaN policy applied here
    # settings restored on exit (ordered), then tip state restored on outer exit
return result
```

Note step ordering: do **not** assert `columns == points`; warn if they differ.
`restore_tip_state` / `restore_module_settings` flags gate whether each scope
actually restores. Factory convenience only:
`nanonis.workflows.bias_spectroscopy()` → `BiasSpectroscopyWorkflow(nanonis.controller)`.

## 4b. Normalization — **sanitized snake_case** runtime keys

The registry sanitizes every arg name via `sanitize_name` at load
([`registry.py:44`](../src/nanonis/command/registry.py)) and `get_recv_types()`
returns the sanitized name, so the decoder keys responses by snake_case (the raw
protocol spelling is preserved as `original_name`). **Do not rename the JSON
fields** to get snake_case — it already happens.

Verified runtime keys for `BiasSpectr.Start`:
`channels_names_size`, `num_channels`, `channels_names`, `data_rows`,
`data_columns`, `data`, `num_parameters`, `parameters`
(note `sanitize_name` maps `Number of …` → `num_…`).

```python
def normalize_bias_spectroscopy_response(response, *, props, requested_points,
        requested_sweeps, include_backward, nan_policy=NaNPolicy.WARN, saved_file=None):
    names = tuple(str(x) for x in response["channels_names"])
    rows  = int(response["data_rows"]); cols = int(response["data_columns"])
    data  = np.array(response["data"], dtype=np.float64, copy=True)

    if data.shape != (rows, cols):
        raise SpectroscopyResponseError(f"shape {data.shape} != ({rows}, {cols})")
    if int(response["num_channels"]) != len(names):
        raise SpectroscopyResponseError("declared channel count != names")
    if len(names) != rows:
        raise SpectroscopyResponseError("cannot map rows to channel names")

    params = normalize_parameters(           # fixed + varying; name=None fallback
        parameter_names_from_props(props),   # props["fixed_parameters"] + props["parameters"]
        response["parameters"], int(response["num_parameters"]))

    if cols != requested_points:
        logger.warning("Start returned %d cols for %d requested points "
                       "(raw result preserved)", cols, requested_points)
    apply_nan_policy(data, nan_policy)
    data.setflags(write=False)
    return BiasSpectroscopyResult(channel_names=names, data=data, data_rows=rows,
        data_columns=cols, parameters=params, requested_points=requested_points,
        requested_sweeps=requested_sweeps, include_backward=include_backward,
        saved_file=saved_file)            # keyword construction (safe as model evolves)
```

**Parameter names are spec-backed**, not merely hypothetical: the protocol states
`Start.parameters` is *fixed values then varying values*, with names from
`PropsGet` (`fixed_parameters + parameters`). The `name=None` fallback stays
because (a) the current `PropsGet` definition is wrong (M0A) and (b) controller
versions vary — never reject a result over a name/length mismatch.

**Multiple sweeps & individual sweeps — do not assume.** The module averages, so
do **not** assume `columns == points * sweeps`. Per `ChsGet` docs, returned names
*may* include averages and individual sweeps when "Save all" is on — i.e.
individual sweeps could appear as extra matrix rows. So: preserve **all**
returned names and rows; M0C determines whether individual sweeps land in the
`Start` response, the autosaved file, or both.

## 5. Storage — plain result + a concrete QCoDeS helper (no sink abstraction)

`run()` returns a plain `BiasSpectroscopyResult`. Because QCoDeS is a **primary
goal**, ship a small, concrete adapter as a planned milestone (M3) — not "only if
a second backend appears", and **not** a general `DataSink` Protocol.

**Two phases, matching the QCoDeS lifecycle.** Parameters must be registered on a
`Measurement` *before* `measurement.run()` yields a `DataSaver`; results are
inserted *inside* the run. A single `add_result(datasaver, ...)` can't register,
so split it:

```python
# nanonis/qcodes/spectroscopy.py
def register_bias_spectroscopy(measurement: Measurement,
                               schema: BiasSpectroscopySchema) -> RegisteredSpectroscopyParameters:
    """Register setpoints + dependent params on the Measurement (pre-run)."""

def add_bias_spectroscopy_result(datasaver: DataSaver,
                                 registered: RegisteredSpectroscopyParameters,
                                 result: BiasSpectroscopyResult,
                                 axes: SpectroscopyAxes) -> None:
    """Insert the result into the open run (post-run)."""
```

**Axis ↔ data consistency.** The setpoint axis is reconstructed from
`effective.points`, but the result permits `data_columns != requested_points`. An
axis of `points` length cannot index `data_columns` samples, so:

```python
if result.data_columns == effective.points:
    axis = reconstruct_forward_axis(...)
else:
    axis = None   # warn: sweep coordinates can't be reconstructed safely
```

Do **not** silently `np.linspace(start, stop, data_columns)` unless M0C proves
that interpretation. Helpers live under `nanonis.qcodes`, imported only there
(keeps `qcodes` optional). A general `DataSink` abstraction comes **only** if a
real second backend (files/HDF5) appears.

## 6. Testing plan

`conftest.py` provides `FakeController` (records `(command, args, timeout)`,
returns scripted responses) and `RecoverableFakeController` (adds `reconnect()`
and can simulate a stale/timed-out socket). Both satisfy the protocols; no
socket/QCoDeS/DB needed.

| Test | Asserts |
| --- | --- |
| `test_state.py::restore_on_success / _exception / _keyboardinterrupt` | restore runs on each exit path |
| `::restore_order` | feedback off → bias → setpoint → feedback on |
| `::best_effort_collects_all_failures` | every field attempted; `StateRestorationError.failures` populated |
| `::restore_after_reconnect_only` | restoration waits for successful `reconnect()` **and** confirmed-stop |
| `::failed_reconnect_or_unverified_stop_is_explicit_failure` | recovery failure → state UNKNOWN, no writes |
| `::stop_and_wait_on_start_timeout` | timeout → reconnect → Stop → StatusGet poll, *before* restoration |
| `test_bias_spectroscopy.py::invalid_config_sends_nothing` | zero sends on bad config |
| `::snapshot_patch_readback_order` | Open → snapshot Get* → ChsSet → PropsSet → LimitsSet → TimingSet → readback → Start |
| `::none_overrides_preserve_existing` | `None` fields reuse snapshot values, not 0.0 |
| `::dual_z_offset_not_collapsed` | `props_z_offset` and `timing_z_offset` sent independently |
| `::long_command_uses_override_timeout` | `Start` sent with `acquisition_timeout`; default restored after |
| `::timed_out_socket_not_reused` | reconnect before next command |
| `test_schema.py::propsget_runtime_recv_names` | recv names == the 12 snake_case keys (regression guard for the field-shift fix) |
| `::propsget_binary_fixture_trailer` | decode bytes ending in two `uint16` + error trailer at correct offset |
| `::propsset_send_field_count` | `PropsSet` encodes exactly 7 send fields |
| `test_result.py::channel_major_matrix` | `(2,256)` → 2 traces, `points_match_request` |
| `::rejects_orientation_and_metadata_mismatch` | wrong rows/shape → `SpectroscopyResponseError` |
| `::duplicate_channel_names_preserved` | `Current (A)` / `Current (A)#2` |
| `::no_bias_channel_required` / `::unexpected_point_count_warns` | lenient, lossless |
| `::nan_raise_carries_partial_result` | `NonFiniteSpectroscopyDataError.result` is the normalized data |
| `::trace_values_are_readonly_views` | trace is a view of the frozen matrix, not a copy |
| `::result_array_is_owned_copy` | mutating source doesn't change result |
| `::axis_none_when_columns_mismatch` | no setpoint axis built when `data_columns != points` |

## 7. Milestones

**M0A — Correct command schemas (blocking).**
*Implemented, awaiting live validation:* `PropsGet` correction (12 fields; spurious
`Channels…` block removed, `Autosave/Show save dialog` trailer appended) and
`PropsSet` (7 send fields: `save_all, num_sweeps, backward_sweep, num_points,
z_offset_m, autosave, show_save_dialog`). *Still missing:* `LimitsSet`,
`TimingSet`, `AdvPropsSet`, `Stop`, `StatusGet`. **Validate** by capturing a raw
live `PropsGet` response, decoding old-vs-corrected, checking the error-trailer
offset, and re-running `scripts/live_test_commands.py`. Add the two schema
regression tests (`test_schema.py`) now so the field-shift fix can't silently
regress. Take `TimingSet`/`PropsSet` arg order from the protocol PDF / `spaik`.

**M0B — Long-command support (blocking; includes Stop/StatusGet).**
Per-command `timeout` on `send()` under an `_io_lock`; connection
invalidation + `reconnect()` + `is_usable` state; **Stop-and-wait recovery** —
`Stop` then bounded `StatusGet` poll to confirm the sweep halted before any
restoration. `Stop` and `StatusGet` are required *here* (not just M0A
completeness) because recovery cannot be correct without them. Touches the
controller — coordinate with Layer 2.

**M0C — Simulator characterization.**
Run and record (names + matrix shape + parameter count) for:

| Case | Points | Sweeps | Backward | Records |
| --- | --- | --- | --- | --- |
| Forward | 8 | 1 | No | names, shape |
| Backward | 8 | 1 | Yes | backward = extra rows or cols? |
| Averaged | 8 | 3 | No | shape stays 8? |
| Averaged + backward | 8 | 3 | Yes | full names + shape |

Plus: Save-all on/off (individual sweeps?), parameter name/value ordering, NaN
behavior. Do not lock any of this into normalization until these pass.

**M1A — Tip-state transaction (independent).** `protocols.py`, `errors.py`, and
`preserve_tip_state` (bias / setpoint / feedback) — uses only `Bias.Get/Set`,
`ZCtrl.SetpntGet/Set`, `ZCtrl.OnOffGet/Set`, all already present. Ordered +
best-effort + `test_state.py`. Not blocked by M0A. Depends on M0B for the
timeout-recovery path tests.

**M1B — Spectroscopy-settings transaction.**
`preserve_bias_spectroscopy_settings` (snapshot-on-entry, ordered restore). This
**depends on M0A** completion + validation, since it reads/writes
`PropsGet`/`PropsSet`/`LimitsSet`/`TimingSet`/`AdvPropsSet`.

**M2 — First workflow.** `models.py`, `result.py`, `bias_spectroscopy.py`
(snapshot/patch/readback, lossless normalization) + tests. Needs M0A setters to
run live.

**M3 — QCoDeS persistence helper.** `nanonis/qcodes/spectroscopy.py`: setpoints,
dependent params, station snapshot, effective-settings metadata.

**M4 — Second workflow.** Prefer scan or data-logging to prove state + protocol
reuse.

## 8. Open decisions

- **Dual Z-offset** — `PropsSet.z_offset_m` vs `TimingSet` Z-offset: same value
  mirrored, independent, or version quirk? `spaik` sets both. Resolve in M0C;
  carry both explicitly until then.
- **Bias-ramp mechanism** — no native command exists; choose stepped `Bias.Set`
  (with a max step) vs. another primitive before relying on "ramp" restoration.
- **Module-restoration order** — channels→limits→timing→props→adv-props is the
  proposed order; confirm on the simulator (adv props affect safety).
- **NaN default** — plan uses WARN (preserve data); confirm vs. RAISE for
  completed STS. (RAISE still carries the partial result regardless.)
- **Channel index upper bound** — `0..127` assumed; verify against the `Signals`
  module's signal count.
- **`TimingSet` exact arg order** — take from the protocol PDF / `spaik`, not
  assumed, when adding it in M0A.

*(Resolved and removed: package discovery — `[tool.setuptools.packages.find]
where=["src"]` already covers `nanonis.workflows` once it has `__init__.py`.
Response-key casing — sanitized snake_case, verified.)*

## Review changelog

**Rev. 4 — accepted from fourth review:**

- **Stop-and-wait recovery** — after a `Start` timeout the sweep may still run;
  reconnect → `Stop` → bounded `StatusGet` poll → verify stopped *before*
  restoring; on failure report state UNKNOWN and write nothing. `Stop`/`StatusGet`
  become blocking **M0B**.
- **Reconnect inside the context-manager bodies**, not the restoration `finally`
  (restoration begins as the exception propagates through the CMs).
- **Dual Z-offset kept explicit** (`props_z_offset` vs `timing_z_offset`); `spaik`
  sets both — never collapse to one until M0C.
- **QCoDeS adapter split** into `register_bias_spectroscopy()` (pre-run) and
  `add_bias_spectroscopy_result()` (post-DataSaver); **no setpoint axis** when
  `data_columns != points`.
- **M1 split** into M1A (tip state, independent of M0A) and M1B (settings, needs
  M0A).
- **Context manager snapshots on entry** (not re-snapshotted in the workflow);
  `Open` before the settings scope.
- **Module-restoration order** specified (channels→limits→timing→props→adv last).
- **Two restore flags** (`restore_tip_state` / `restore_module_settings`).
- **`RAISE` carries the partial result** (`NonFiniteSpectroscopyDataError.result`
  + diagnostics); normalize first, then apply policy.
- **Traces are read-only views**, not per-channel copies; ownership enforced at
  the constructor boundary.
- **`_io_lock`** around the timeout-swap + full transaction (defensive, for
  shared-controller concurrency).
- **Schema regression tests** for the corrected `PropsGet` (runtime names + binary
  trailer fixture) and `PropsSet` field count.
- Stale coverage updated: `PropsSet` now exists in the config.

**Rev. 3 — accepted from third review:**

- **Runtime keys are sanitized snake_case** (`channels_names`, `data_rows`,
  `num_channels`, …) via `sanitize_name`. **Retracts the rev. 2 "Title-Case
  keys" claim and its "normalize the JSON" recommendation** — both wrong.
- **`PropsGet` is mis-defined** → re-derive in M0A (corroborated by `spaik`).
- **Per-command timeout + socket invalidation/reconnect** for long acquisitions
  (controller had a single fixed 10 s timeout).
- **Snapshot-and-patch config** with `None` overrides (was: `0.0` defaults that
  would overwrite valid settings); typed `BiasSpectroscopySettings`.
- **Ordered, best-effort restoration**; separate `preserve_tip_state` /
  `preserve_bias_spectroscopy_settings` scopes; corrected the `spaik`
  "masks the error" wording.
- **Own the result array** (`np.array(..., copy=True)`) — `setflags` on a view
  could freeze the caller's buffer.
- **Explicit `NaNPolicy`** (default WARN, not the reviewer's RAISE — see §3c).
- **Parameter naming is spec-backed** (fixed+varying from `PropsGet`), with
  `name=None` fallback while `PropsGet` is broken / versions vary.
- **Do not pre-exclude individual sweeps** from `Start`; characterize in M0C.
- **Dropped `ResultCapture`**; `run() -> Result`; QCoDeS helper promoted to a
  planned **M3** (concrete adapter under `nanonis.qcodes`, no `DataSink`).
- Resolved package-discovery and structural-validation open items.

**Rev. 2 — accepted from second review (still in force):** lossless
channel-major matrix + ordered names; read back effective settings;
`points_match_request` diagnostic-only; `SweepAxis` as reconstructed setpoint;
`include_backward: bool` + tristate wire; no `columns == points * sweeps`;
simulator characterization before encoding behavior. **Resolved via `spaik`:**
orientation is channel-major (transpose evidence); parameter NaN guard ported.

## Reference: real command schemas (from `configs/commands` + `spaik`)

- `Bias.Set(value V)` · `Bias.Get() -> value V` · `Bias.RangeGet()` (preflight bounds)
- `ZCtrl.OnOffGet/Set(status)` · `ZCtrl.SetpntGet/Set(setpoint)`
- `BiasSpectr.Open()` · `BiasSpectr.ChsSet(num, indexes)` — **only setter present**
- `BiasSpectr.PropsSet / LimitsSet / TimingSet / AdvPropsSet / Stop / StatusGet` — **MISSING, add in M0A**
- `BiasSpectr.PropsGet` (corrected, per `spaik`): `Save all(H), Number of sweeps(i),
  Backward sweep(H), Number of points(i), Parameters size(i), Number of parameters(i),
  Parameters(1Dstr), Fixed parameters size(i), Number of fixed parameters(i),
  Fixed parameters(1Dstr), Autosave(H), Show save dialog(H)`
- `BiasSpectr.TimingGet/Set` (8): `Z averaging time, Z offset (m), Initial settling,
  Max slew rate (V/s), Settling, Integration, End settling, Z control time`
- `BiasSpectr.Start(Get data, Save base name)` → runtime keys: `channels_names_size,
  num_channels, channels_names, data_rows, data_columns, data, num_parameters, parameters`
