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
- **Error detection**: Parses Nanonis error responses
- **Debug mode**: Verbose logging for troubleshooting
- **QCoDeS integration**: Full support for QCoDeS Station and Measurement

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

# Create instrument
nanonis = NanonisInstrument(
    'nanonis',
    host='127.0.0.1',
    port=6501,
    config_path='configs/nanonis_tcp.yaml'
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

## Configuration Files

| File | Commands | Source |
|------|----------|--------|
| `configs/nanonis_tcp.yaml` | 148 | Original JSON (SPM) |
| `configs/nanonis_tramea.yaml` | 264 | nanonis_tramea package (TRAMEA) |

### Command Modules (tramea)

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

## Directory Structure

```
qcodes_nanonis/
├── src/nanonis/
│   ├── protocol/           # Layer 1: TCP Communication
│   ├── command/            # Layer 2: Command Interface
│   └── qcodes/             # Layer 3: QCoDeS Integration
├── configs/
│   ├── nanonis_tcp.yaml    # SPM commands (148)
│   └── nanonis_tramea.yaml # TRAMEA commands (264)
├── tests/
├── scripts/
│   ├── convert_json_to_yaml.py
│   └── extract_tramea_commands.py
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
| `string` | str | Length-prefixed UTF-8 |
| `array_*` | np.ndarray | 1D arrays |
| `matrix_*` | np.ndarray | 2D arrays |

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
