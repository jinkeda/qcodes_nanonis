# Workflow Layer — Implementation Plan

Status: proposed (rev. 7) · Date: 2026-06-29

Rev. 7 folds in a seventh review round and is the **planning-complete** revision:
the next step is code, not another plan pass (no further design change is worth
much without simulator evidence). Key structural changes: a single
**`RestorationTransaction`** coordinator (replacing naive nested context managers,
which let an outer failure mask an inner one); **`TransportState`** split from
instrument state (with a `RecoveryReport`); an **injected
`BiasSpectroscopySafetyPolicy`** instead of hidden limits; slew-rate÷0 guard;
backward-aware QCoDeS voltage axes; timestamp + recovery-timing validation; and a
clean **framing (TCP) vs body-semantics (decoder)** validation split.

Earlier rounds (verified against the code, still in force): receive-timeout is
mis-classified as `NanonisConnectionError` (focused test — dead `except
socket.timeout`); `NanonisProtocolError` is never raised (no header validation);
`FolMe` is XY positioning, not a bias ramp; Z-offset model is one restorable
`z_offset` from `TimingGet`; acquire-first QCoDeS. **No live controller is
reachable, so M0A hardware validation remains pending.** See the
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
├── state.py              # RestorationTransaction + TipState / settings participants
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

- **Fix timeout classification first (verified bug).** Living test: a receive
  timeout currently surfaces as `NanonisConnectionError`, not
  `NanonisTimeoutError`, because `_recv_exact` catches `socket.error` — and
  `socket.timeout` is a subclass of it — so the outer `except socket.timeout` in
  `_receive_response` is **dead code**. Reorder in `_recv_exact`:

  ```python
  try:
      chunk = self._socket.recv(size - len(data))
  except socket.timeout:
      raise                                  # let _receive_response classify it
  except socket.error as exc:
      raise NanonisConnectionError(...) from exc
  ```

  Tests (M0B): timeout while receiving header; timeout mid-body; connection closed
  mid-body; timeout marks the connection unusable. Without this, the whole recovery
  category in §1b mis-routes timeouts.

- **Make `NanonisProtocolError` real (verified gap), with a clean ownership
  split.** It is imported but **never raised** (`grep 'raise NanonisProtocolError'`
  → 0 hits), and `_receive_response` parses the header without validating it.
  Split validation by layer:
  - **TCP / transport — framing only:** header fully received; body size ≥ 0 and ≤
    a configured max; returned command name matches the request; header flags
    well-formed. **Do not** make the transport layer aware of command-specific
    error trailers.
  - **Command decoder — body semantics:** expected fields consumed; error trailer
    present and complete; error-description length valid; no unexplained trailing
    bytes.

  Confirm the **response** flag values from the protocol manual before enforcing
  them — do not infer them from the request header (which always sends `send=1,
  reserved=0`; the response flags differ). (M0B.)

- `send(..., timeout: float | None = None)` — temporarily apply the per-command
  timeout on the TCP client, restore the previous value in a `finally`.
  **`timeout=None` means "use the controller default", never "wait forever".**
  The workflow never passes `None` for `Start`; it passes
  `config.acquisition_timeout` or, when that is `None`, a bound **computed from the
  effective timing** (see formula below). Falling back to the 10 s socket default
  for a real sweep is a bug.

- **Acquisition-timeout formula** — guard the slew-rate divisor (the effective
  Nanonis value may be 0 / non-finite):

  ```python
  point_time    = integration_time + settling_time
  sampling_time = points * point_time
  if np.isfinite(maximum_slew_rate) and maximum_slew_rate > 0:
      slew_time = abs(stop_voltage - start_voltage) / maximum_slew_rate
  else:
      slew_time = 0.0; logger.warning("cannot estimate slew-limited duration")
  one_direction = max(sampling_time, slew_time)        # sweep may be slew-limited
  directions    = 2 if include_backward else 1
  estimate = (initial_settling + z_control_time + z_averaging_time
              + sweeps * directions * one_direction + end_settling)
  timeout  = estimate * 1.5 + 5.0                        # multiplicative + comms margin
  ```

  When timing can't be estimated safely, use a larger fallback margin **or** require
  an explicit `acquisition_timeout`. Record **both** `estimated_acquisition_duration`
  and `acquisition_timeout_used` on the result — a single `estimated_timeout` is
  ambiguous when the user supplied an override. The rev-5 sketch under-counts
  initial/end settling, Z averaging/control, and the slew-limited duration.
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

- **Recovery triggers are a category, not just timeout/KeyboardInterrupt.** Any
  transport failure that leaves the request/response stream out of sync must
  trigger recovery:

  ```python
  RECOVERABLE_TRANSPORT_ERRORS = (NanonisTimeoutError,
                                  NanonisConnectionError,   # reset, partial read
                                  NanonisProtocolError)     # malformed/incomplete header/body
  ```

  A *decode* error after a **fully received** response is NOT the same as an
  incomplete read — the connection is still in sync. **Keep transport state and
  instrument state separate.** The generic controller tracks only **transport**
  health; the spectroscopy recovery helper tracks whether the *module* stopped:

  ```python
  class TransportState(Enum):            # on the controller — transport only
      DISCONNECTED = "disconnected"
      READY = "ready"
      DESYNCHRONIZED = "desynchronized"  # partial response
      RECOVERING = "recovering"

  @dataclass(frozen=True)
  class RecoveryReport:                  # from the spectroscopy recovery helper
      transport_ready: bool
      spectroscopy_stopped: bool | None  # None = unknown (e.g. interrupted recovery)
      errors: tuple[BaseException, ...]
      @property
      def restoration_allowed(self) -> bool:
          return self.transport_ready and self.spectroscopy_stopped is True
  ```

  Restoration proceeds only when `RecoveryReport.restoration_allowed`.

- **Recovery contract = invalidate → reconnect → Stop-and-wait → restore.** If
  `Start` fails, two things are true at once: its response may still be in the
  socket, **and the sweep may still be running on the instrument**. Reconnecting
  clears the stale socket but does *not* stop the sweep. Put the sequence in **one
  reusable helper**, not inline in every workflow:

  ```python
  def recover_bias_spectroscopy(client: RecoverableCommandClient, *,
          timeout: float, poll_interval: float = 0.1) -> RecoveryReport:
      client.reconnect()
      if status_is_stopped(client):        # query FIRST — if already stopped,
          return RecoveryReport(client.transport_ready, True, ())  # Stop failure isn't fatal
      try:
          client.send("BiasSpectr.Stop")
          deadline = time.monotonic() + timeout
          while time.monotonic() < deadline:   # monotonic, bounded
              if status_is_stopped(client):
                  return RecoveryReport(client.transport_ready, True, ())
              time.sleep(poll_interval)
          return RecoveryReport(client.transport_ready, False, ())   # not stopped → no writes
      except KeyboardInterrupt as second:
          # Do NOT swallow it: recovery incomplete, stop unknown, no restoration writes.
          return RecoveryReport(client.transport_ready, None, (second,))
  ```

  **Second-interrupt behavior is explicit:** a `KeyboardInterrupt` *during* recovery
  marks recovery incomplete (`spectroscopy_stopped=None`), keeps the last-known
  transport state, skips restoration writes, and the workflow raises a
  `StateRestorationError` carrying **both** interrupts. This makes `Stop` and
  `StatusGet` **blocking M0B requirements**.

## 2. `state.py` — one restoration coordinator (build & test first)

**Do not nest two independent context managers.** Naive nesting cannot satisfy the
four requirements at once — both scopes best-effort, failures from both *combined*,
all writes gated on recovery state, and a successful result attached if cleanup
fails — and worse, an outer tip-restore failure can **mask** the inner
settings-restore error. Keep the **state models separate and typed**
(`TipState`, `BiasSpectroscopySettings`) but coordinate them through **one
transaction** that restores participants in reverse order and raises a single
aggregated error:

```python
with RestorationTransaction(client, recovery=recover_bias_spectroscopy) as tx:
    tx.preserve("tip", TipState.snapshot(client))
    client.send("BiasSpectr.Open")
    original = tx.preserve("bias_spectroscopy", BiasSpectroscopySettings.snapshot(client))
    ...                                  # configure, acquire
    result = normalize(...)
    tx.attach_result(result)             # carried out even if later cleanup fails
# on exit: if RecoveryReport.restoration_allowed, restore in REVERSE order
# (bias_spectroscopy first, then tip), best-effort, collecting every failure:
#   StateRestorationError(original_error=..., recovery_error=...,
#       failures={"bias_spectroscopy.timing": ..., "tip.bias": ..., "tip.feedback": ...},
#       result=result)
```

This is **not** a god object: snapshot/restore logic stays in the typed state
classes; only failure coordination, ordering, and write-gating are centralized.

Requirements (revised from review):

- **Restore on every exit** — normal, Nanonis error, timeout, `KeyboardInterrupt`
  (`try/finally`, covering `BaseException`).
- **Ordered restoration**, based on lab procedure, not field order:
  1. disable feedback if it must be off to change bias safely,
  2. restore bias toward the initial value (see ramp note),
  3. restore current setpoint,
  4. re-enable feedback **last**.
- **Best-effort**: do not stop at the first failed field. Attempt every
  remaining safe operation, collect all failures, **and carry the acquired
  result** — a sweep can complete successfully and then fail during cleanup;
  losing valid data because restoration failed is unacceptable:

  ```python
  class StateRestorationError(WorkflowError):
      def __init__(self, *, original_error, failures, recovery_error=None, result=None):
          self.original_error = original_error   # what the body raised (may be KeyboardInterrupt)
          self.recovery_error = recovery_error   # failure during reconnect/stop-and-wait
          self.failures = failures               # {"bias":..., "setpoint":..., "settings":...}
          self.result = result                   # normalized result if acquisition succeeded
  ```

  The workflow attaches `result` whenever normalization completed before cleanup
  failed. **Recovery-failure precedence:** raise `... from original_error` so the
  cause is chained; document that the **top-level type is no longer
  `KeyboardInterrupt`**, so callers must inspect `original_error` to detect an
  interrupt. Salvage pattern for callers:

  ```python
  try:
      result = workflow.run(config)
  except StateRestorationError as exc:
      if exc.result is None:
          raise
      persist_result(exc.result)   # don't discard valid data because cleanup failed
      raise
  ```

- **Module-settings restoration also has an order** (tip state is not the only
  thing with ordering): ensure spectroscopy stopped → restore channels → limits
  → timing → properties → **advanced properties last** (Z-controller hold / reset
  bias affect safety). Exact order confirmed on the simulator in M0C.
- After a `Start` timeout/interrupt, restoration runs **only after** a successful
  `reconnect()` **and** confirmed-stopped (§1b); a failed reconnect or unverified
  stop is an explicit restoration failure — report state UNKNOWN, do not write.
- Never `assert` for hardware safety. Log every state change at INFO.

**Recovery runs inside the transaction body, before restoration.** The transaction
restores on exit, so recovery must produce its `RecoveryReport` *first* — in the
body — and hand it to the transaction:

```python
with RestorationTransaction(client, recovery=recover_bias_spectroscopy) as tx:
    tx.preserve("tip", TipState.snapshot(client)); client.send("BiasSpectr.Open")
    tx.preserve("bias_spectroscopy", BiasSpectroscopySettings.snapshot(client))
    try:
        response = client.send("BiasSpectr.Start", 1, config.save_base_name,
                               timeout=resolve_acquisition_timeout(config, effective))
    except RECOVERABLE_TRANSPORT_ERRORS + (KeyboardInterrupt,) as exc:
        tx.record_recovery(recover_bias_spectroscopy(
            client, timeout=config.recovery_timeout,
            poll_interval=config.status_poll_interval), origin=exc)
        raise
    tx.attach_result(normalize(...))
```

On exit the transaction restores **only if** `RecoveryReport.restoration_allowed`;
otherwise it skips all writes and raises with `recovery_error` set — it never
writes on a `DESYNCHRONIZED` link or when the module stop is unconfirmed.

> **Bias restoration is a blocking lab-safety decision (M1A is not done until it
> is settled).** There is **no native Nanonis bias-ramp command** — only the
> instantaneous `Bias.Set`. (`FolMe` is **XY positioning** — `FolMe.XYPosGet/Set` —
> not bias; it is *not* a ramp primitive.) `spaik` ramps externally (ADwin) or via
> stepped writes. Make the policy explicit:
>
> ```python
> class BiasRestoreMode(Enum):
>     DIRECT = "direct"; STEPPED = "stepped"; EXTERNAL = "external"
>
> @dataclass(frozen=True)
> class BiasRampPolicy:
>     max_step: float
>     dwell_time: float
>     zero_crossing_policy: "ZeroCrossingPolicy"
> ```
>
> Lab questions that must be answered (not just software): is crossing zero
> permitted? feedback off during the ramp? what if the ramp is interrupted
> halfway? restore current setpoint before or after bias? `DIRECT` may be
> acceptable since the initial value was a safe operating point — the risk is the
> size of the jump from the sweep's end voltage.

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

    # ONE restorable Z-offset. PropsGet does NOT return a Z-offset (verified);
    # only TimingGet does. PropsSet *writes* one but it can't be read back on the
    # Props path, so a separate props_z_offset cannot be snapshotted/restored.
    # Apply this single value to BOTH PropsSet and TimingSet. M0C tests whether
    # they are truly one setting; only split if both become independently readable.
    z_offset: float | None = None            # m, -> PropsSet AND TimingSet
    integration_time: float | None = None    # s
    settling_time: float | None = None        # s
    maximum_slew_rate: float | None = None    # V/s

    save_base_name: str = ""
    # None = compute a conservative bound from effective timing (NOT the 10 s
    # socket default); see §1b. Explicit values override.
    acquisition_timeout: float | None = None  # s
    recovery_timeout: float = 15.0            # s, bound on stop-and-wait
    status_poll_interval: float = 0.1         # s
    restore_tip_state: bool = True
    restore_module_settings: bool = True

    def __post_init__(self):
        # Structural validation only (no I/O). Hardware preflight is a separate
        # live phase (§4) because it needs a connection.
        if self.points < 2:
            raise ValueError("points must be >= 2")
        if self.sweeps < 1:
            raise ValueError("sweeps must be >= 1")
        if not self.channel_indexes:
            raise ValueError("need >= 1 channel")
        if len(set(self.channel_indexes)) != len(self.channel_indexes):
            raise ValueError("duplicate channel indexes")
        if any(i < 0 for i in self.channel_indexes):     # structural only; existence
            raise ValueError("channel index must be >= 0")  # is checked in preflight
            # NB: no hard-coded upper bound here — preflight validates each index
            # against the live Signals.NamesGet length (§4), not a magic 127.
        if not (np.isfinite(self.start_voltage) and np.isfinite(self.stop_voltage)):
            raise ValueError("non-finite voltage")
        if self.start_voltage == self.stop_voltage:
            raise ValueError("start_voltage == stop_voltage")
        for t in (self.integration_time, self.settling_time, self.maximum_slew_rate):
            if t is not None and not (np.isfinite(t) and t > 0):   # finite AND positive
                raise ValueError("timing/slew overrides must be finite and > 0")
        if self.acquisition_timeout is not None and not (
                np.isfinite(self.acquisition_timeout) and self.acquisition_timeout > 0):
            raise ValueError("acquisition_timeout must be finite and > 0 when provided")
        # recovery-timing fields are not optional, so always validate them:
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")
        if self.status_poll_interval <= 0:
            raise ValueError("status_poll_interval must be > 0")
        if self.status_poll_interval > self.recovery_timeout:
            raise ValueError("status_poll_interval cannot exceed recovery_timeout")
        if self.z_offset is not None and not np.isfinite(self.z_offset):
            raise ValueError("z_offset must be finite when provided")
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
    autosave: bool
    show_save_dialog: bool
    timing: "BiasSpectroscopyTiming"     # 8 fields (TimingGet) — OWNS the only readable z_offset
    advanced: "BiasSpectroscopyAdvanced"
    limits: tuple[float, float]
```

There is **no** `props_z_offset` field: `PropsGet` does not return a Z-offset, so
the only snapshot-able Z-offset is `timing.z_offset`. The tristate wire value for
backward (and other checkbox setters) is `1 = enabled, 2 = disabled, 0 = no change`.

> **Z-offset is write-asymmetric (M0C).** Verified: `PropsSet` *takes* a Z-offset
> but `PropsGet` does **not** return one — only `TimingGet` does. `spaik` reads the
> `TimingGet` value and feeds it to both setters. So restoration snapshots
> `timing.z_offset`, and applying an override sends the **same** value to both
> `PropsSet` and `TimingSet`:
>
> ```python
> z = config.z_offset if config.z_offset is not None else original.timing.z_offset
> client.send("BiasSpectr.PropsSet", ..., z, ...)
> client.send("BiasSpectr.TimingSet", ..., z, ...)
> ```
>
> M0C checks whether writing either setter changes `TimingGet`. Only introduce two
> independent fields if both can be independently **read and restored** — a
> write-only value cannot support transactional restoration.

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
    name: str | None                # None when PropsGet names are unavailable or the
    value: float                    # controller version is incompatible

@dataclass(frozen=True)
class BiasSpectroscopyResult:
    channel_names: tuple[str, ...]
    data: FloatArray                # channel-major (data_rows, data_columns)
    data_rows: int
    data_columns: int
    parameters: tuple[SpectroscopyParameter, ...]
    requested_config: "BiasSpectroscopyConfig"      # provenance
    effective_settings: "BiasSpectroscopySettings"  # authoritative (read back)
    # Acquisition happened BEFORE the QCoDeS run opens (acquire-first, §5), so the
    # dataset's own timestamp is NOT the measurement time. Capture it here.
    acquisition_started_at: datetime         # tz-aware UTC wall-clock (provenance)
    acquisition_finished_at: datetime        # tz-aware UTC wall-clock
    acquisition_duration: float              # seconds, from time.monotonic()
    estimated_acquisition_duration: float    # the §1b estimate
    acquisition_timeout_used: float          # what was actually passed to Start
    save_base_name: str = ""
    saved_paths: tuple[str, ...] = ()   # populated only after discovering real files
    # requested_points / _sweeps / include_backward are derivable from
    # effective_settings; kept off the result to avoid a second source of truth.

    def __post_init__(self):
        # Own + freeze the array here so DIRECT construction is also safe — the
        # normalizer therefore needs no second copy (chosen over "normalizer is the
        # only constructor"). object.__setattr__ because the dataclass is frozen.
        data = np.array(self.data, dtype=np.float64, copy=True)
        data.setflags(write=False)
        object.__setattr__(self, "data", data)
        if data.shape != (self.data_rows, self.data_columns):
            raise ValueError("matrix shape != declared (rows, columns)")
        if len(self.channel_names) != self.data_rows:
            raise ValueError("channel-name count != data rows (orientation)")
        # timestamp provenance must be sane
        if self.acquisition_started_at.tzinfo is None or self.acquisition_finished_at.tzinfo is None:
            raise ValueError("acquisition timestamps must be timezone-aware (UTC)")
        if self.acquisition_duration < 0:
            raise ValueError("acquisition_duration must be non-negative")
        if self.acquisition_finished_at < self.acquisition_started_at:
            raise ValueError("finish precedes start")

    @property
    def points_match_request(self) -> bool:    # DIAGNOSTIC only
        return self.data_columns == self.effective_settings.points

    def traces(self) -> tuple[SpectroscopyTrace, ...]:
        seen, out = {}, []
        for name, values in zip(self.channel_names, self.data):
            occ = seen.get(name, 0); seen[name] = occ + 1
            out.append(SpectroscopyTrace(name, occ, values))
        return tuple(out)
```

`find_channels` / `get_unique_channel` / `__iter__` are deferred to the first
real consumer.

**Immutability — decided: own + freeze in `__post_init__`** (above). A frozen
dataclass does **not** freeze its NumPy arrays, and `np.asarray` may return a
*view* of the caller's buffer. Enforcing the copy/freeze in `__post_init__`
centralizes the invariant and makes **direct** construction safe, so the
normalizer does not copy again. **Traces are read-only views, not copies:** once
the base matrix is owned and read-only, `self.data[index]` is itself a read-only
view — no per-channel copy (avoids N copies). Reconstructed sweep axes are owned
separately (not slices of `data`) and frozen the same way.

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
yields NaNs — RAISE would discard real data). **Build the result first, then
inspect, then apply the policy** — so even `RAISE` carries a fully-constructed,
inspectable result (the rev-4 pseudocode applied the policy before the result
existed, leaving nothing to attach):

```python
result = BiasSpectroscopyResult(channel_names=names, data=data, data_rows=rows,
            data_columns=cols, parameters=params, requested_config=config,
            effective_settings=effective)
diagnostics = inspect_non_finite_data(result)     # nan_count, inf_count,
                                                  # fully_nan_channels, affected_channels
if nan_policy is NaNPolicy.WARN:
    log_non_finite_diagnostics(diagnostics)
elif nan_policy is NaNPolicy.RAISE and diagnostics.has_non_finite:
    raise NonFiniteSpectroscopyDataError(result, diagnostics)
return result

class NonFiniteSpectroscopyDataError(WorkflowError):
    def __init__(self, result, diagnostics):
        self.result = result          # fully-normalized, inspectable
        self.diagnostics = diagnostics
        super().__init__(...)
```

Distinguish *any* NaN, *entire-channel* NaN, and non-finite (`±inf`). Ported from
`spaik`'s `NaNinDataError` but as a configurable policy that never loses data.

## 4. `bias_spectroscopy.py` — first vertical

**Safety limits are injected, not hard-coded.** The "approved" Z-offset/slew/bias
limits and the bias-restoration choice live in a setup-specific policy passed to the
workflow — so they are reviewable, testable, and versionable per rig:

```python
@dataclass(frozen=True)
class BiasSpectroscopySafetyPolicy:
    max_abs_bias: float
    max_abs_z_offset: float
    min_slew_rate: float
    max_slew_rate: float
    bias_restore_mode: BiasRestoreMode
    bias_ramp: BiasRampPolicy | None
    allow_zero_crossing: bool

class BiasSpectroscopyWorkflow:
    def __init__(self, client: CommandClient, *, safety_policy: BiasSpectroscopySafetyPolicy):
        self._client = client
        self._safety = safety_policy

    def run(self, config: BiasSpectroscopyConfig, *,
            unsafe_skip_preflight: bool = False) -> BiasSpectroscopyResult:
        ...
```

No `capture` parameter — tests inspect the returned result directly; QCoDeS
persistence is a caller-side helper (§5).

**Hardware preflight is mandatory by default** (this is a hardware-safety
workflow). Unless `unsafe_skip_preflight=True`, the first live phase verifies — with
**concrete, fail-closed** rules, all bounds drawn from `safety_policy`:

- **Bias range:** `Bias.RangeGet` returns *textual* range descriptions + an active
  index, so define how the text is parsed to a numeric ±limit, plus
  `policy.max_abs_bias` as an absolute hard limit independent of parsing.
  **Unknown range format → fail closed** (raise) unless `unsafe_skip_preflight`.
  Start/stop must fit the active range.
- **Channel existence:** each index `< len(Signals.NamesGet())` — checked against
  the **live** signal count, not a hard-coded `0..127`.
- **Z-offset** within `policy.max_abs_z_offset`; **`maximum_slew_rate`** within
  `[policy.min_slew_rate, policy.max_slew_rate]`.
- **Not already running:** `StatusGet` shows no spectroscopy in progress.

Structural validation (§3) stays I/O-free; preflight is the first command phase.
(Full preflight needs `Signals.NamesGet` + `StatusGet`, so it lands incrementally
with M0B.)

Participants are snapshotted on `tx.preserve(...)`; the workflow does not
re-snapshot. `Open` happens before the settings snapshot, since some getters may
require the module open:

```python
preflight(client, config, self._safety) unless unsafe_skip_preflight   # first live phase
with RestorationTransaction(client, recovery=recover_bias_spectroscopy) as tx:
    tx.preserve("tip", TipState.snapshot(client))
    client.send("BiasSpectr.Open")
    original = tx.preserve("bias_spectroscopy", BiasSpectroscopySettings.snapshot(client))
    z = config.z_offset if config.z_offset is not None else original.timing.z_offset
    original.patch(config).apply(client, z_offset=z)   # send z to PropsSet AND TimingSet
    effective = read_back_effective(client)            # tristate 0 = no change → readback authoritative
    try:
        response = client.send("BiasSpectr.Start", 1, config.save_base_name,
                               timeout=resolve_acquisition_timeout(config, effective))
    except RECOVERABLE_TRANSPORT_ERRORS + (KeyboardInterrupt,) as exc:
        tx.record_recovery(recover_bias_spectroscopy(client,
            timeout=config.recovery_timeout, poll_interval=config.status_poll_interval),
            origin=exc); raise
    result = normalize_bias_spectroscopy_response(
                 response, props=effective.props, config=config,
                 effective=effective, nan_policy=...)   # builds result, then NaN policy
    tx.attach_result(result)
# on exit: if restoration_allowed → restore bias_spectroscopy then tip (reverse), best-effort
return result
```

Note: do **not** assert `columns == points`; warn if they differ.
`restore_tip_state` / `restore_module_settings` flags gate whether each scope
restores. If acquisition succeeded but restoration fails, the raised
`StateRestorationError` carries `result` (§2). Factory convenience only:
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
def normalize_bias_spectroscopy_response(response, *, props, config, effective,
        nan_policy=NaNPolicy.WARN):
    names = tuple(str(x) for x in response["channels_names"])
    rows  = int(response["data_rows"]); cols = int(response["data_columns"])
    data  = response["data"]            # the model owns + freezes it in __post_init__

    if np.shape(data) != (rows, cols):
        raise SpectroscopyResponseError(f"shape {np.shape(data)} != ({rows}, {cols})")
    if int(response["num_channels"]) != len(names):
        raise SpectroscopyResponseError("declared channel count != names")
    if len(names) != rows:
        raise SpectroscopyResponseError("cannot map rows to channel names")

    params = normalize_parameters(           # fixed + varying; name=None fallback
        parameter_names_from_props(props),   # props["fixed_parameters"] + props["parameters"]
        response["parameters"], int(response["num_parameters"]))

    if cols != effective.points:
        logger.warning("Start returned %d cols for %d effective points "
                       "(raw result preserved)", cols, effective.points)

    result = BiasSpectroscopyResult(channel_names=names, data=data, data_rows=rows,
        data_columns=cols, parameters=params, requested_config=config,
        effective_settings=effective)    # __post_init__ copies+freezes data
    # build-first, THEN NaN policy (see §3c) — RAISE carries this result
    return apply_nan_policy(result, nan_policy)
```

**Parameter names are spec-backed**, not merely hypothetical: the protocol states
`Start.parameters` is *fixed values then varying values*, with names from
`PropsGet` (`fixed_parameters + parameters`). The `name=None` fallback stays
because (a) the corrected `PropsGet` definition is **awaiting live validation**
(M0A — no controller was reachable) and (b) controller versions vary — never
reject a result over a name/length mismatch.

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

**Acquire-first, persist-second.** QCoDeS needs parameters registered *before*
`measurement.run()`, but the **channel names aren't known until `Start` returns**
(backward / individual-sweep rows change the schema). Since `Start` returns the
complete matrix in one shot — there is no streaming during acquisition — register
*from the finished result*, then open the run and insert:

```python
# nanonis/qcodes/spectroscopy.py
result = workflow.run(config)
measurement, registered = create_bias_spectroscopy_measurement(experiment, result)
with measurement.run() as datasaver:
    add_bias_spectroscopy_result(datasaver, registered, result)
```

`create_bias_spectroscopy_measurement` derives the parameter schema from
`result.channel_names` + `result.effective_settings` and registers setpoints +
dependent params. A *prepared* workflow (`workflow.prepare(config)` exposing a
schema before acquisition) is only worth it if the DB run must physically
encompass hardware acquisition — defer it; acquire-first is correct here.

**Always provide a `sample_index` axis; add voltage carefully — one forward axis
does NOT fit backward traces.** `axis=None` would leave channel data with no
setpoint. Register every channel against an always-present `sample_index`. Adding a
voltage setpoint requires more than `data_columns == points`: with backward enabled,
forward and backward rows have **opposite** voltage axes despite identical lengths,
so a single forward axis would mislabel the backward traces.

```python
sample_index = np.arange(result.data_columns)            # always valid
eff = result.effective_settings
if not eff.include_backward and result.data_columns == eff.points:
    voltage_axes = forward_axis                          # single axis is safe
elif eff.include_backward and trace_directions_are_characterized:  # needs M0C
    voltage_axes = {t.unique_name: (backward_axis if t.is_backward else forward_axis)
                    for t in result.traces()}
else:
    voltage_axes = None                                  # warn; sample_index still valid
```

So **M0C must establish how backward traces are identified** before M3 adds voltage
setpoints for them. Do **not** silently `np.linspace(start, stop, data_columns)`.

**Sanitize QCoDeS identifiers.** Channel names contain spaces, parens, slashes,
`[bwd]`, `#2`, and duplicates; QCoDeS parameter identifiers must be stable and
collision-free. Store both, keyed by occurrence:

```python
RegisteredTrace(parameter_name="current_a_2", label="Current (A)", occurrence=1)
```

Tests must cover duplicate and backward (`[bwd]`) names.

**Persist `acquisition_started_at` / `_finished_at` / `_duration`** (§3c) as run
metadata — with acquire-first, the dataset's own timestamp is the *persist* time,
not the measurement time. Helpers live under `nanonis.qcodes`, imported only there
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
| `::recover_returns_early_if_already_stopped` | `recover_*` queries status first; Stop failure non-fatal when stopped |
| `::restoration_error_carries_result` | acquisition OK + cleanup fails → `StateRestorationError.result` set |
| `::transaction_restores_reverse_order` | settings restored before tip state |
| `::transaction_aggregates_both_scopes` | tip + settings failures both in `.failures`, neither masked |
| `::second_interrupt_marks_unknown` | KeyboardInterrupt in recovery → `spectroscopy_stopped is None`, no writes, both interrupts carried |
| `::restoration_allowed_gate` | writes only when `transport_ready and spectroscopy_stopped is True` |
| `test_bias_spectroscopy.py::invalid_config_sends_nothing` | zero sends on bad config |
| `::recovery_timing_validation` | `recovery_timeout`/`status_poll_interval` > 0 and poll ≤ recovery |
| `::nonfinite_overrides_rejected` | non-finite timing / slew / z_offset → ValueError |
| `::zero_slew_rate_no_div0` | `maximum_slew_rate == 0` → slew_time 0 + warning, no crash |
| `::safety_policy_bounds_enforced` | z_offset / slew / bias outside `safety_policy` → preflight raises |
| `::preflight_mandatory_unless_skipped` | bad range / unknown channel / already-running → raises before Start |
| `::snapshot_patch_readback_order` | Open → snapshot Get* → ChsSet → PropsSet → LimitsSet → TimingSet → readback → Start |
| `::none_overrides_preserve_existing` | `None` fields reuse snapshot values, not 0.0 |
| `::z_offset_sent_to_both_setters` | one `z_offset` → identical value to PropsSet and TimingSet |
| `::recoverable_error_category` | reset / partial / protocol error all trigger recovery, not just timeout |
| `::long_command_uses_computed_or_override_timeout` | `Start` timeout = override, else computed; never the 10 s default |
| `::timed_out_socket_not_reused` | reconnect before next command |
| `test_tcp.py::timeout_receiving_header / _mid_body` | classified as `NanonisTimeoutError`, not `NanonisConnectionError` |
| `::connection_closed_mid_body` | → `NanonisConnectionError` (distinct from timeout) |
| `::timeout_marks_transport_desynchronized` | `TransportState.DESYNCHRONIZED`, not `READY` |
| `::protocol_error_on_bad_header` | negative/over-max body size, command-name mismatch → `NanonisProtocolError` |
| `test_schema.py::propsget_runtime_recv_names` | recv names == the 12 snake_case keys (regression guard for the field-shift fix) |
| `::propsget_binary_fixture_trailer` | decode bytes ending in two `uint16` + error trailer at correct offset |
| `::propsset_send_field_count` | `PropsSet` encodes exactly 7 send fields |
| `test_result.py::channel_major_matrix` | `(2,256)` → 2 traces, `points_match_request` |
| `::rejects_orientation_and_metadata_mismatch` | wrong rows/shape → `SpectroscopyResponseError` |
| `::duplicate_channel_names_preserved` | `Current (A)` / `Current (A)#2` |
| `::no_bias_channel_required` / `::unexpected_point_count_warns` | lenient, lossless |
| `::nan_raise_carries_partial_result` | build-first: `NonFiniteSpectroscopyDataError.result` is normalized |
| `::trace_values_are_readonly_views` | trace is a view of the frozen matrix, not a copy |
| `::direct_construction_is_frozen` | `__post_init__` copies+freezes even on direct construction |
| `::result_carries_effective_settings` | `result.effective_settings` is the read-back authority |
| `::timestamps_validated` | naive tzinfo / negative duration / finish-before-start → ValueError |
| `::result_array_is_owned_copy` | mutating source doesn't change result |
| `test_qcodes.py::sample_index_axis_always_present` | channels registered vs `sample_index` even when voltage unknown |
| `::no_forward_axis_for_backward_traces` | with backward enabled, single forward axis is NOT applied to all rows |
| `::voltage_setpoint_added_only_forward_only` | voltage added only when `not include_backward and columns == points` |
| `::param_identifiers_sanitized_and_unique` | duplicate / `[bwd]` names → stable collision-free ids + labels |

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

**M0B — Long-command support + transport correctness (blocking).**
Layer-1/2 fixes first: **fix timeout classification** in `_recv_exact` (verified
bug — timeouts mis-report as `NanonisConnectionError`) and **add header
validation** so `NanonisProtocolError` is actually raised. Then per-command
`timeout` on `send()` under an `_io_lock`; `reconnect()` + **`TransportState`**
tracking (transport only); **Stop-and-wait recovery** returning a `RecoveryReport`
(`Stop` → bounded `StatusGet` poll → confirm halted before any restoration).
`Stop`/`StatusGet` are required here, not just for M0A coverage. Framing validation
in transport, body-semantics validation in the decoder (§1b). Touches the
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

**M0D — Restoration coordinator + safety policy.** `RestorationTransaction`
(reverse-order, aggregated `StateRestorationError`, recovery-gated writes) and the
injected `BiasSpectroscopySafetyPolicy`. Pure-Python, testable with `FakeController`;
sequence it before M1 so both tip and settings scopes plug into one coordinator.

**M1A — Tip-state participant (independent).** `protocols.py`, `errors.py`, and the
`TipState` snapshot/restore registered into the transaction — uses only
`Bias.Get/Set`, `ZCtrl.SetpntGet/Set`, `ZCtrl.OnOffGet/Set`, all already present.
Ordered + best-effort + `test_state.py`. Not blocked by M0A. **Blocked on a lab
decision:** the bias-restoration policy (`BiasRestoreMode` / `BiasRampPolicy` /
`allow_zero_crossing` — §2, §4) must be settled before M1A is "done".

**M1B — Spectroscopy-settings participant.**
`BiasSpectroscopySettings` snapshot/restore registered into the transaction
(ordered restore), using **one restorable `z_offset`** (from `TimingGet`) applied to
both setters until M0C proves otherwise. **Depends on M0A** completion + validation,
since it reads/writes `PropsGet`/`PropsSet`/`LimitsSet`/`TimingSet`/`AdvPropsSet`.

**M2 — First workflow.** `models.py`, `result.py`, `bias_spectroscopy.py`
(snapshot/patch/readback, lossless normalization), **mandatory hardware
preflight**, **result carries `effective_settings`** + tests. Needs M0A setters to
run live.

**M3 — QCoDeS persistence (acquire-first).** `nanonis/qcodes/spectroscopy.py`:
register the schema *from the finished result*, then insert under
`measurement.run()`; setpoints, dependent params, station snapshot,
effective-settings metadata. Prepared-workflow execution deferred.

**M4 — Second workflow.** Prefer scan or data-logging to prove state + protocol
reuse.

## 8. Open decisions

- **Z-offset relationship** — `PropsSet` writes a Z-offset that only `TimingGet`
  can read back. Does writing either setter change `TimingGet`? `spaik` feeds the
  `TimingGet` value to both. Resolve in M0C; until then there is **one** restorable
  `z_offset` (from `TimingGet`) sent to both setters — never a second field.
- **Bias-restoration policy (BLOCKING M1A; lab decision).** Now hosted in the
  injected `BiasSpectroscopySafetyPolicy` (§4): `BiasRestoreMode`
  (DIRECT/STEPPED/EXTERNAL) + `BiasRampPolicy` + `allow_zero_crossing`. No native
  bias-ramp command exists (`FolMe` is XY, not bias). Still to answer with the lab:
  zero-crossing allowed? feedback off during ramp? interrupted-halfway behavior?
  setpoint before/after bias?
- **Safety-limit values** — `max_abs_bias`, `max_abs_z_offset`, slew min/max are
  per-rig; supplied via the policy, confirmed with the lab.
- **Module-restoration order** — channels→limits→timing→props→adv-props is the
  proposed order; confirm on the simulator (adv props affect safety).
- **NaN default** — plan uses WARN (preserve data); confirm vs. RAISE for
  completed STS. (RAISE still carries the partial result regardless.)
- **`TimingSet` exact arg order** — take from the protocol PDF / `spaik`, not
  assumed, when adding it in M0A.

*(Resolved: channel-index bound — no magic `0..127`; preflight checks each index
against the live `Signals.NamesGet` length.)*

*(Resolved and removed: package discovery — `[tool.setuptools.packages.find]
where=["src"]` already covers `nanonis.workflows` once it has `__init__.py`.
Response-key casing — sanitized snake_case, verified.)*

## Review changelog

**Rev. 7 — accepted from seventh review (planning-complete):**

- **Single `RestorationTransaction` coordinator** replaces nested context managers
  (which let an outer tip-restore failure mask the inner settings error). Separate
  typed state models; centralized failure coordination, reverse-order restore,
  aggregated `StateRestorationError`, recovery-gated writes, result attach.
- **Split `TransportState` (controller, transport-only) from instrument state**;
  the recovery helper returns a `RecoveryReport(transport_ready, spectroscopy_stopped,
  errors)` with a `restoration_allowed` gate. Drops the conflated `ConnectionState`.
- **Guard slew-rate ÷ 0 / non-finite** in the timeout formula; record both
  `estimated_acquisition_duration` and `acquisition_timeout_used` (was the
  ambiguous `estimated_timeout`).
- **Validate `recovery_timeout` / `status_poll_interval`** (>0, poll ≤ recovery) and
  use `isfinite AND >0` for timing/slew overrides.
- **Backward-aware QCoDeS voltage axes** — a single forward axis must not label
  backward traces; voltage added only forward-only (or per-trace once M0C
  characterizes direction). `sample_index` always present.
- **Injected `BiasSpectroscopySafetyPolicy`** — limits and restore mode are
  per-rig, reviewable/testable, not hidden constants.
- **Framing (TCP) vs body-semantics (decoder) validation split**; don't infer
  response flags from the request header.
- **Concrete second-interrupt behavior** (`spectroscopy_stopped=None`, no writes,
  both interrupts carried).
- **Timestamp validation** in `__post_init__` (tz-aware, duration ≥ 0, finish ≥ start).
- Wording: "living test" → "focused test"; `SpectroscopyParameter` comment "PropsGet
  bug" → "unavailable / incompatible controller version".
- New milestone **M0D** (coordinator + safety policy).

**Rev. 6 — accepted from sixth review (3 claims verified against the code):**

- **Timeout mis-classification (focused test).** `_recv_exact`'s `except socket.error`
  swallows `socket.timeout` (a subclass) → it surfaces as `NanonisConnectionError`;
  the outer `except socket.timeout` is dead code. Reorder to catch `socket.timeout`
  first. → M0B + `test_tcp.py`.
- **`NanonisProtocolError` never raised** (grep: 0 hits) — header is parsed but not
  validated. Add body-size / command-name / flag / completeness checks. → M0B.
- **`FolMe` is XY positioning** (`FolMe.XYPosGet/Set`), **not** a bias-ramp
  primitive — removed from the ramp options.
- **Bias-restoration safety policy** (`BiasRestoreMode` / `BiasRampPolicy`) is a
  **blocking lab decision** for M1A.
- **`ConnectionState` enum** replaces the `is_usable` bool; restoration requires
  `READY`.
- **Fuller acquisition-timeout formula** (initial/end settling, Z averaging/control,
  slew-limited duration, ×1.5 + 5 s); estimate recorded in result metadata.
- **Always provide a `sample_index` QCoDeS axis**; voltage setpoint only when
  `data_columns == points`.
- **Acquisition timestamps** on the result (tz-aware UTC + monotonic duration),
  persisted as metadata — acquire-first means the dataset timestamp isn't the
  measurement time.
- **Sanitized, collision-free QCoDeS identifiers** (`RegisteredTrace` name + label +
  occurrence).
- **Concrete preflight** (textual `Bias.RangeGet` parsing, fail-closed on unknown
  format, channel existence vs live `Signals.NamesGet`).
- **Recovery-failure precedence** — `StateRestorationError` gains `recovery_error`,
  chains `from original_error`; top-level type is no longer `KeyboardInterrupt`, so
  callers inspect `original_error`. Salvage-on-restoration-failure pattern documented.
- Wording: "PropsGet is wrong" → "corrected, **awaiting live validation**" (no
  controller reachable).

**Rev. 5 — accepted from fifth review:**

- **Z-offset model fixed (the key correction).** Verified `PropsGet` returns **no**
  Z-offset; only `TimingGet` does. A `props_z_offset` snapshot is therefore
  impossible (write-only path). Collapsed to **one** `z_offset` owned by
  `timing`, applied to both `PropsSet` and `TimingSet`. Retracts rev-4's
  `props_z_offset` / `timing_z_offset` split.
- **Build the result before applying NaN policy** — rev-4 applied the policy first,
  so `RAISE` had no result to attach.
- **QCoDeS is acquire-first** — channel names aren't known until `Start` returns, so
  register from the finished result, then insert. (Replaces rev-4's register-before-run.)
- **`StateRestorationError` carries `result`** — don't lose good data when only
  cleanup fails.
- **Recovery triggers are a category** (`RECOVERABLE_TRANSPORT_ERRORS`), and the
  controller (which knows if the response was fully received) decides usability.
- **Reusable `recover_bias_spectroscopy()` helper** — query status first, monotonic
  bounded poll, survive a second KeyboardInterrupt, never falsely claim success.
- **`timeout=None` = controller default, never infinite**; `Start` uses an explicit
  override or a bound computed from effective timing — never the 10 s socket default.
- **Result carries `requested_config` + `effective_settings`** (authoritative);
  dropped the redundant `requested_points/_sweeps/include_backward` fields.
- **`saved_file` → `save_base_name` + `saved_paths`** (`Start` returns no path).
- **Ownership enforced in `__post_init__`** (copy + freeze) so direct construction
  is safe; normalizer no longer double-copies.
- **Mandatory hardware preflight** for `run()` unless `unsafe_skip_preflight=True`.
- Stale reference fixed: `PropsSet` is present.

**Rev. 4 — accepted from fourth review:**

- **Stop-and-wait recovery** — after a `Start` timeout the sweep may still run;
  reconnect → `Stop` → bounded `StatusGet` poll → verify stopped *before*
  restoring; on failure report state UNKNOWN and write nothing. `Stop`/`StatusGet`
  become blocking **M0B**.
- **Reconnect inside the context-manager bodies**, not the restoration `finally`
  (restoration begins as the exception propagates through the CMs).
- **Dual Z-offset kept explicit** (`props_z_offset` vs `timing_z_offset`).
  **— superseded in rev 5:** `PropsGet` returns no Z-offset, so this is one field.
- **QCoDeS adapter split** into `register_bias_spectroscopy()` (pre-run) and
  `add_bias_spectroscopy_result()` (post-DataSaver). **— refined in rev 5 to
  acquire-first** (register from the finished result). **No setpoint axis** when
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
- `BiasSpectr.Open()` · **Present setters:** `ChsSet`, `PropsSet`.
  **Missing (add in M0A/M0B):** `LimitsSet`, `TimingSet`, `AdvPropsSet`, `Stop`,
  `StatusGet`.
- `BiasSpectr.PropsGet` (corrected, per `spaik`): `Save all(H), Number of sweeps(i),
  Backward sweep(H), Number of points(i), Parameters size(i), Number of parameters(i),
  Parameters(1Dstr), Fixed parameters size(i), Number of fixed parameters(i),
  Fixed parameters(1Dstr), Autosave(H), Show save dialog(H)` — **no Z-offset**.
- `BiasSpectr.PropsSet` (7): `Save all(H), Number of sweeps(i), Backward sweep(H),
  Number of points(i), Z offset (m)(f), Autosave(H), Show save dialog(H)` — **has a
  write-only Z-offset** (not echoed by PropsGet).
- `BiasSpectr.TimingGet/Set` (8): `Z averaging time, Z offset (m), Initial settling,
  Max slew rate (V/s), Settling, Integration, End settling, Z control time` — the
  **only readable Z-offset**.
- `BiasSpectr.Start(Get data, Save base name)` → runtime keys: `channels_names_size,
  num_channels, channels_names, data_rows, data_columns, data, num_parameters, parameters`
