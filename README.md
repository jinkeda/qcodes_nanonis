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

# Use in Measurement
meas = Measurement()
meas.register_parameter(nanonis.bias.voltage)

# Direct Layer 2 access if needed
nanonis.send('Custom.Command', arg1, arg2)

# Clean up
nanonis.close()
```

## Directory Structure

```
qcodes_nanonis/
├── src/nanonis/
│   ├── __init__.py
│   ├── protocol/           # Layer 1: TCP Communication
│   │   ├── exceptions.py   # Custom exceptions
│   │   └── tcp_client.py   # Low-level TCP client
│   ├── command/            # Layer 2: Command Interface
│   │   ├── registry.py     # Command definitions loader
│   │   ├── encoder.py      # Value encoding/decoding
│   │   ├── controller.py   # Main controller class
│   │   └── proxies.py      # Convenience wrappers
│   └── qcodes/             # Layer 3: QCoDeS Integration
│       ├── instrument.py   # NanonisInstrument class
│       └── channels/       # QCoDeS channels
│           ├── bias.py
│           └── scan.py
├── configs/
│   └── nanonis_tcp.yaml    # Command definitions (148 commands)
├── tests/
│   ├── test_protocol.py
│   ├── test_encoder.py
│   └── test_controller.py
├── scripts/
│   └── convert_json_to_yaml.py  # Config conversion tool
└── pyproject.toml
```

## Supported Types

| Type | Python | Description |
|------|--------|-------------|
| `float32` | float | 32-bit float |
| `float64` | float | 64-bit float |
| `int16` | int | 16-bit signed |
| `int32` | int | 32-bit signed |
| `uint16` | int | 16-bit unsigned |
| `uint32` | int | 32-bit unsigned |
| `bool` | bool | Boolean (4 bytes) |
| `string` | str | Length-prefixed UTF-8 |
| `array_float32` | np.ndarray | 1D float32 array |
| `array_int32` | np.ndarray | 1D int32 array |
| `array_string` | list[str] | 1D string array |
| `matrix_float32` | np.ndarray | 2D float32 array |
| `matrix_string` | list[list[str]] | 2D string array |

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Configuration

Commands are defined in `configs/nanonis_tcp.yaml`. To regenerate from JSON:

```bash
python scripts/convert_json_to_yaml.py
```

## License

MIT License

## References

- [Nanonis TCP Protocol Documentation](TCPProtocol_SPM.pdf)
- [QCoDeS Documentation](https://qcodes.github.io/Qcodes/)
- [nanonisTCP](https://github.com/New-Horizons-SPM/nanonisTCP)
