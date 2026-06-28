# QCoDeS Nanonis

A Python library for communicating with Nanonis SPM controllers, with optional QCoDeS integration.

## Architecture

The library uses a **3-layer architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: QCoDeS Integration (Optional)                     │
│  NanonisInstrument + BiasChannel + ScanChannel              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Command Interface (Core)                          │
│  NanonisController.send(command_name, *args) → result       │
│  CommandRegistry + CommandEncoder + CommandDecoder          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Protocol/Transport                                │
│  NanonisTCPClient.send_raw(command, body) → response        │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Configuration-driven**: Commands defined in YAML, easy to extend
- **Type coercion**: Automatic conversion to correct numpy types
- **Protocol-correct arrays**: 1D/2D arrays are framed per the Nanonis spec — no
  embedded length prefix; the element count comes from a separate preceding
  field, which the decoder resolves automatically
- **Error detection**: Parses Nanonis error responses
- **Debug mode**: Verbose logging for troubleshooting
- **QCoDeS integration**: Full support for QCoDeS Station and Measurement
- **Live validation**: A harness that exercises every command against a real or
  simulated controller and reports which definitions are correct

## Installation

```bash
# Basic installation (Layer 1 + 2)
pip install -e .

# With QCoDeS support (Layer 3)
pip install -e ".[qcodes]"

# Development
pip install -e ".[dev]"
```

## Quick Start

### Standalone Usage (Layer 2)

```python
from nanonis.command import NanonisController

with NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml') as ctrl:
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
ctrl = NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml')
ctrl.debug = True  # Enable verbose logging
ctrl.connect()
ctrl.send('Bias.Get')  # Will log type coercion, bytes, errors
```

### QCoDeS Integration (Layer 3)

```python
from nanonis.qcodes import NanonisInstrument
from qcodes import Station, Measurement

nanonis = NanonisInstrument(
    'nanonis',
    host='127.0.0.1',
    port=6501,
    config_path='configs/nanonis_tcp.yaml',
)

# Use QCoDeS parameters
nanonis.bias.voltage(0.5)
print(nanonis.bias.voltage())

# Use in Station
station = Station()
station.add_component(nanonis)

# Direct Layer 2 access if needed
nanonis.send('Custom.Command', arg1, arg2)

nanonis.close()
```

## Command Definitions

Command definitions flow through a small pipeline so the wire format stays
correct and corrections are easy to maintain:

```
configs/nanonis_tcp_overrides.yaml      # hand-corrected definitions (edit here)
        │  scripts/apply_overrides_to_json.py
        ▼
configs/nanonis_tcp_auto.json  ──split_commands.py──▶  configs/commands/<Module>.json
        │  scripts/convert_json_to_yaml.py   (size-field normalization + overrides)
        ▼
configs/nanonis_tcp.yaml                # loaded by the controller
```

- `nanonis_tcp_auto.json` is generated from `TCPProtocol_SPM.pdf` by
  `generate_nanonis_tcp.py`.
- `nanonis_tcp_overrides.yaml` is the source of truth for hand-corrected
  commands (the PDF parser mis-derives some). Overrides are merged over the
  auto-generated entries and survive regeneration.
- `convert_json_to_yaml.py` emits the YAML the codec loads. It drops the
  redundant `<x> size` field before each scalar `string` (our `string` type is
  self-describing) while keeping array size/count fields, which are real on the
  wire.

To add or fix a command:

```bash
# 1. edit configs/nanonis_tcp_overrides.yaml
python scripts/apply_overrides_to_json.py   # sync into JSON + re-split per module
python scripts/convert_json_to_yaml.py      # regenerate nanonis_tcp.yaml
python scripts/live_test_commands.py        # verify against the controller
```

### Configuration files

| File | Commands | Source |
|------|----------|--------|
| `configs/nanonis_tcp.yaml` | 148 | Generated from `nanonis_tcp_auto.json` (+ overrides) |
| `configs/nanonis_tramea.yaml` | 264 | `nanonis_tramea` package (TRAMEA) |
| `configs/nanonis_tcp_auto.json` | 148 | Parsed from `TCPProtocol_SPM.pdf` |
| `configs/nanonis_tcp_overrides.yaml` | 12 | Hand-corrected definitions |
| `configs/commands/<Module>.json` | — | Per-module split of the JSON (reference) |

### Command modules (tramea)

| Module | Commands | Description |
|--------|----------|-------------|
| 3DSwp | 44 | 3D Sweeper |
| OsciHR | 40 | High-Resolution Oscilloscope |
| HSSwp | 34 | High-Speed Sweeper |
| LockIn | 30 | Lock-In Amplifier |
| Script | 15 | Script Control |
| Util | 15 | Utilities |
| 1DSwp | 14 | 1D Sweeper |
| MCVA5 | 14 | Multichannel Voltage Amplifier |
| UserOut | 14 | User Outputs |
| PICtrl | 10 | PI Controller |

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
> it against a Nanonis **simulator** or a rig where neutral writes are harmless.

## Directory Structure

```
qcodes_nanonis/
├── src/nanonis/
│   ├── protocol/                       # Layer 1: TCP transport + exceptions
│   ├── command/                        # Layer 2: registry, encoder/decoder, controller, proxies
│   └── qcodes/                         # Layer 3: QCoDeS instrument + channels
├── configs/
│   ├── nanonis_tcp.yaml                # generated config loaded by the codec
│   ├── nanonis_tcp_auto.json           # PDF-derived JSON source
│   ├── nanonis_tcp_overrides.yaml      # hand-corrected definitions
│   ├── nanonis_tramea.yaml             # TRAMEA commands
│   └── commands/                       # per-module split JSON (reference)
├── scripts/
│   ├── convert_json_to_yaml.py         # JSON (+ overrides) -> YAML
│   ├── apply_overrides_to_json.py      # overrides -> JSON source
│   ├── split_commands.py               # JSON -> per-module files
│   ├── live_test_commands.py           # live validation harness
│   └── extract_tramea_commands.py
├── reports/                            # live-test reports + command_fix_plan.md
├── legacy/                             # pre-refactor terminal + IPInstrument driver
├── tests/
├── generate_nanonis_tcp.py             # TCPProtocol_SPM.pdf -> JSON codegen
├── TCPProtocol_SPM.pdf
└── pyproject.toml
```

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
- [nanonis_tramea](https://pypi.org/project/nanonis-tramea/)
