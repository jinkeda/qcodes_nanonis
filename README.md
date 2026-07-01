# QCoDeS Nanonis

A Python library for communicating with Nanonis SPM controllers, with optional QCoDeS integration.

## Architecture

A **`protocol → command` core**, with **`workflows`** (transactional measurement
recipes) and **`qcodes`** (optional adapters) as **parallel** consumers of the
command layer. Neither consumer depends on the other; QCoDeS persistence adapters
consume completed workflow results — workflows never create or return QCoDeS
datasets.

```
            ┌──────────────────────────┐      ┌──────────────────────────┐
            │  workflows/  (recipes)   │      │  qcodes/  (optional)     │
            │  BiasSpectroscopyWorkflow│      │  NanonisInstrument +     │
            │  ScanWorkflow → results  │      │  Bias/Scan channels      │
            └────────────┬─────────────┘      └────────────┬─────────────┘
                         │  send(...)                       │  send(...)
                         ▼                                  ▼
            ┌─────────────────────────────────────────────────────────────┐
            │  command/  (core)                                           │
            │  NanonisController.send(name, *args, timeout=) → result     │
            │  CommandRegistry + CommandEncoder + CommandDecoder          │
            └─────────────────────────────┬───────────────────────────────┘
                                          ▼
            ┌─────────────────────────────────────────────────────────────┐
            │  protocol/  (transport)                                     │
            │  NanonisTCPClient.send_raw(...) · TransportState · errors   │
            └─────────────────────────────────────────────────────────────┘

            workflow result ──→ qcodes/ persistence adapter ──→ QCoDeS dataset
```

The `workflows` layer depends on the command API plus the protocol layer's stable
error/state types (`NanonisTimeoutError`, `TransportState`, …); it imports nothing
from `qcodes`.

## Features

- **Configuration-driven**: Commands defined in per-module JSON, easy to extend
- **Type coercion**: Automatic conversion to correct numpy types
- **Protocol-correct arrays**: 1D/2D arrays are framed per the Nanonis spec — no
  embedded length prefix; the element count comes from a separate preceding
  field, which the decoder resolves automatically
- **Error detection**: Parses Nanonis error responses; classifies timeout vs.
  connection vs. protocol failures and tracks transport state
- **Transactional workflows**: end-to-end measurement recipes with typed config,
  Nanonis state snapshot, recovery-gated best-effort restoration, and lossless
  results (bias spectroscopy and one-frame scanning implemented)
- **Debug mode**: Verbose logging for troubleshooting
- **QCoDeS integration**: Optional QCoDeS Station/Measurement support and an
  acquire-first persistence adapter for results
- **Live validation**: A harness that exercises every command against a real
  controller and reports which definitions are correct. Workflows are validated
  against **real Nanonis hardware over a real socket**, with fast `FakeController`
  unit tests for regressions

## Installation

```bash
# Core (protocol + command + workflows)
pip install -e .

# With optional QCoDeS adapters
pip install -e ".[qcodes]"

# Development
pip install -e ".[dev]"
```

## Quick Start

### Standalone command usage

```python
from nanonis.command import NanonisController

with NanonisController('127.0.0.1', 6501, 'configs/commands') as ctrl:
    # Set bias voltage
    ctrl.send('Bias.Set', 0.5)

    # Get bias voltage
    voltage = ctrl.send('Bias.Get')
    print(f"Bias: {voltage} V")

    # Set scan frame
    ctrl.send('Scan.FrameSet', 0, 0, 100e-9, 100e-9, 0)

    # List available commands
    print(ctrl.list_commands('Bias'))
```

### Debug Mode

```python
ctrl = NanonisController('127.0.0.1', 6501, 'configs/commands')
ctrl.debug = True  # Enable verbose logging
ctrl.connect()
ctrl.send('Bias.Get')  # Will log type coercion, bytes, errors
```

### Transactional Workflows

High-level measurement recipes that snapshot Nanonis state, run an acquisition,
normalize a self-describing result, and restore state (recovery-gated,
best-effort) on every exit path. Bias spectroscopy and one-frame scanning use
the same recovery and result-preservation contract.

```python
from nanonis.command import NanonisController
from nanonis.workflows import (
    BiasRestoreMode,
    BiasSpectroscopyConfig,
    BiasSpectroscopySafetyPolicy,
    BiasSpectroscopyWorkflow,
)

# Rig-specific safety limits are INJECTED — replace with lab-approved values.
policy = BiasSpectroscopySafetyPolicy(
    max_abs_bias=2.0, max_abs_z_offset=100e-9,
    min_slew_rate=1e-3, max_slew_rate=10.0,
    bias_restore_mode=BiasRestoreMode.DIRECT,
    bias_ramp=None, allow_zero_crossing=False,
)
config = BiasSpectroscopyConfig(
    start_voltage=-0.2, stop_voltage=0.2, points=401,
    channel_indexes=(0, 24), sweeps=2, save_base_name="sts/example",
)

with NanonisController('127.0.0.1', 6501, 'configs/commands') as ctrl:
    result = BiasSpectroscopyWorkflow(ctrl, safety_policy=policy).run(config)

print(result.channel_names)      # rows are channels
print(result.data.shape)         # (channels, samples)
print(result.effective_settings) # authoritative controller readback
```

If acquisition succeeds but restoration fails, the raised `StateRestorationError`
still carries the acquired `result` so valid data is never lost.

#### One-frame scan workflow

The scan workflow snapshots the complete scan configuration, applies a typed
patch, performs safety preflight against the live piezo range, starts one
non-continuous frame, collects immutable 2-D channel images, and restores the
original settings. The limits below are examples only; replace them with values
approved for the scanner and tip in use.

```python
from nanonis.command import NanonisController
from nanonis.workflows import ScanConfig, ScanRegion, ScanSafetyPolicy, ScanWorkflow

policy = ScanSafetyPolicy(
    max_pixels=1024,
    max_lines=1024,
    piezo_safety_margin=20e-9,
    min_line_time=1e-3,
    max_line_time=10.0,
    min_linear_speed=1e-12,
    max_linear_speed=1e-3,
)
# ScanConfig is the stable recipe (how to measure); the frame is a separate,
# round-trippable ScanRegion (where/what to measure) passed to run(config, region).
config = ScanConfig(
    channel_indexes=(0, 24),
    direction="up",
    pixels=256,
    lines=256,
    forward_line_time=0.25,
    backward_line_time=0.10,
    autosave="next",
    series_name="topography",
    data_directions=("forward", "backward"),
)
region = ScanRegion(center_x=0.0, center_y=0.0, width=100e-9, height=100e-9)

with NanonisController("127.0.0.1", 6501, "configs/commands") as ctrl:
    result = ScanWorkflow(ctrl, safety_policy=policy).run(config, region)

print(result.saved_path)
for image in result.images:
    print(image.name, image.direction, image.scan_direction, image.data.shape)
```

`ScanRegion` is round-trippable — `ScanRegion.snapshot(ctrl)` reads the current
frame, `.patch(width=...)` overrides fields, `.apply(ctrl)` writes it back — and
`region=None` leaves the current frame untouched. This recipe/region split makes
grid/tile loops trivial: `for region in tiles: workflow.run(config, region)`.

See `examples/scan_workflow_live_demo.ipynb` for the guarded live-hardware
walkthrough and `reports/scan_workflow_walkthrough.md` for recovery, timeout,
normalization, and known-limit details. QCoDeS scan persistence is implemented
(`nanonis.qcodes.scan`, 2-D meshgrid setpoints + provenance); workflow acquisition
itself does not depend on QCoDeS.

### QCoDeS Integration (optional)

```python
from nanonis.qcodes import NanonisInstrument
from qcodes import Station, Measurement

nanonis = NanonisInstrument(
    'nanonis',
    host='127.0.0.1',
    port=6501,
    config_path='configs/commands',
)

# Use QCoDeS parameters
nanonis.bias.voltage(0.5)
print(nanonis.bias.voltage())

# Use in Station
station = Station()
station.add_component(nanonis)

# Direct command access if needed
nanonis.send('Custom.Command', arg1, arg2)

nanonis.close()
```

## Command Definitions

The per-module files in `configs/commands/` are the single source of truth.
The controller loads every `*.json` file in that directory and normalizes the
raw protocol type codes at runtime.

To add or fix a command:

```bash
# Edit the relevant module file, for example configs/commands/TCPLog.json
python scripts/live_test_commands.py
```

To regenerate definitions from the protocol PDF, write directly to the same
directory and merge the existing hand-corrected definitions:

```bash
python generate_nanonis_tcp.py TCPProtocol_SPM.pdf configs/commands \
    --existing configs/commands
```

## Live Testing & Validation

`scripts/live_test_commands.py` sends every command in a config to a running
controller, validates each response against its definition, and writes a
categorized Markdown report.

```bash
python scripts/live_test_commands.py --host 127.0.0.1 --port 6501
```

Result categories:

| Category | Meaning |
|----------|---------|
| `PASS` | Sent, decoded, no error |
| `MODULE_UNAVAILABLE` | Definition fine; the module isn't running in this session |
| `PROTOCOL_MISMATCH` | Wrong **send** types (Nanonis could not unflatten the request) |
| `DECODE_ERROR` / `STRUCTURE_MISMATCH` | Wrong **recv** definition |
| `NANONIS_ERROR` | Runtime/state error (e.g. invalid argument, file not found) |

Destructive meta-commands (e.g. `Util.Quit`) are skipped by default. Reports and
the command fix plan live under `reports/`.

> ⚠️ The harness sends state-changing commands with neutral arguments. Only run
> it against a rig where neutral writes are harmless.

## Directory Structure

```
qcodes_nanonis/
├── src/nanonis/
│   ├── protocol/                       # transport: TCP client, TransportState, exceptions
│   ├── command/                        # core: registry, encoder/decoder, controller, proxies
│   ├── workflows/                      # transactional measurement recipes
│   │   ├── protocols.py, errors.py, state.py, models.py   # shared toolkit
│   │   ├── spectroscopy/               #   bias spectroscopy (implemented)
│   │   ├── scan/                       #   one-frame scan workflow (implemented)
│   │   └── tunnel/ datalog/ atom_tracking/                # planned verticals
│   ├── qcodes/                         # optional adapters; spectroscopy + scan persistence
│   └── data/                           # STM data models + readers (planned)
├── configs/
│   └── commands/                       # canonical per-module JSON definitions
├── scripts/
│   └── live_test_commands.py           # live validation harness
├── reports/                            # plans, walkthrough, blueprint, live-test reports
├── examples/                           # spectroscopy + scan live-demo notebooks
├── legacy/                             # pre-refactor terminal + IPInstrument driver
├── tests/                              # incl. tests/workflows/ (FakeController doubles)
├── generate_nanonis_tcp.py             # PDF -> per-module JSON codegen
├── TCPProtocol_SPM.pdf
└── pyproject.toml
```

See `reports/blueprint.md` for the architecture vision and roadmap,
`reports/workflow_layer_walkthrough.md` for what is implemented, and
`reports/scan_workflow_walkthrough.md` for the implemented scan vertical.

## Supported Types

| Type | Python | Description |
|------|--------|-------------|
| `float32` | float | 32-bit float |
| `float64` | float | 64-bit float |
| `int16` / `int32` | int | Signed integers |
| `uint16` / `uint32` | int | Unsigned integers |
| `bool` | bool | Boolean (4 bytes) |
| `string` | str | Length-prefixed UTF-8 (self-describing) |
| `array_*` | np.ndarray / list | 1D arrays |
| `matrix_*` | np.ndarray / list | 2D arrays |

Arrays carry **no** embedded length prefix: the element count (and, for string
arrays, the size in bytes) are separate fields that precede the array in the
command definition, exactly as in the Nanonis TCP protocol.

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT License

## References

- [Nanonis TCP Protocol Documentation](TCPProtocol_SPM.pdf)
- [QCoDeS Documentation](https://qcodes.github.io/Qcodes/)
