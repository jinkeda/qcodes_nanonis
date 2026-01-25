# QCoDeS Nanonis

A Python library for communicating with Nanonis SPM controllers, with optional QCoDeS integration and an optional high-performance Rust backend.

## Features

- **3-Layer Architecture**: Clean separation of protocol, command, and application layers
- **Configuration-Driven**: Commands defined in YAML files for easy extension
- **354 Commands Supported**: Full SPM (148) + TRAMEA modules (206)
- **Type Safety**: Automatic conversion to correct numpy types with validation
- **Rust Backend**: Optional 10-50x speedup for encoding/decoding operations
- **Debug Mode**: Verbose logging for troubleshooting protocol issues
- **QCoDeS Integration**: Full support for QCoDeS Station and Measurement

## Architecture

```
                           ┌─────────────────────────────────────────┐
                           │  Layer 3: QCoDeS Integration (Optional) │
                           │  NanonisInstrument + Channels           │
                           └────────────────┬────────────────────────┘
                                            │
                           ┌────────────────▼────────────────────────┐
                           │  Layer 2: Command Interface (Core)      │
                           │  NanonisController + Registry + Codec   │
                           └────────────────┬────────────────────────┘
                                            │
┌──────────────────────────┐   ┌────────────▼────────────────────────┐
│  nanonis_core (Rust)     │◄──│  Layer 1: Protocol/Transport        │
│  Optional Performance    │   │  NanonisTCPClient                   │
└──────────────────────────┘   └─────────────────────────────────────┘
```

## Installation

```bash
# Basic installation (pure Python)
pip install -e .

# With QCoDeS support
pip install -e ".[qcodes]"

# Development (includes testing and linting tools)
pip install -e ".[dev]"
```

### Rust Backend (Optional)

For enhanced performance, install the Rust backend:

```bash
# Requires Rust toolchain (https://rustup.rs)
cd nanonis_core
pip install maturin
maturin develop --release
```

The library automatically uses the Rust backend when available and falls back to pure Python otherwise.

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

    # Set scan frame (center_x, center_y, width, height, angle)
    ctrl.send('Scan.FrameSet', 0, 0, 100e-9, 100e-9, 0)

    # Start scanning
    ctrl.send('Scan.Action', 0, 1)  # direction=0, action=start

    # List available commands
    print(ctrl.list_commands('Bias'))
```

### Debug Mode

```python
ctrl = NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml')
ctrl.debug = True  # Enable verbose logging
ctrl.connect()

# Will log: type coercion, encoded bytes, response parsing, errors
ctrl.send('Bias.Get')
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
print(f"Voltage: {nanonis.bias.voltage()} V")

# Use in Station
station = Station()
station.add_component(nanonis)

# Direct Layer 2 access for custom commands
result = nanonis.send('Custom.Command', arg1, arg2)

nanonis.close()
```

### Using Proxy Classes

```python
from nanonis.command import NanonisController
from nanonis.command.proxies import BiasProxy, ScanProxy

with NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml') as ctrl:
    # Convenient proxy interfaces
    bias = BiasProxy(ctrl)
    scan = ScanProxy(ctrl)

    bias.set(0.5)
    print(f"Bias: {bias.get()} V")

    scan.set_frame(0, 0, 100e-9, 100e-9, 0)
    scan.start()
```

## Configuration Files

| File | Commands | Source |
|------|----------|--------|
| `configs/nanonis_tcp.yaml` | 148 | Original Nanonis SPM protocol |
| `configs/nanonis_tramea.yaml` | 206 | TRAMEA extension modules |

### SPM Modules (nanonis_tcp.yaml)

| Module | Description |
|--------|-------------|
| Bias | Voltage control and pulse |
| Scan | Scan frame, motion, buffer |
| ZCtrl | Z-controller parameters |
| Motor | Coarse motor movement |
| AutoApproach | Automatic tip approach |
| Current | Current measurement |
| Piezo | Piezo drive control |
| SafeTip | Tip protection |

### TRAMEA Modules (nanonis_tramea.yaml)

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

## Supported Data Types

| Type | Python | Size | Description |
|------|--------|------|-------------|
| `float32` | float | 4 bytes | 32-bit IEEE 754 |
| `float64` | float | 8 bytes | 64-bit IEEE 754 |
| `int16` | int | 2 bytes | Signed 16-bit |
| `int32` | int | 4 bytes | Signed 32-bit |
| `uint16` | int | 2 bytes | Unsigned 16-bit |
| `uint32` | int | 4 bytes | Unsigned 32-bit |
| `bool` | bool | 4 bytes | Boolean (Nanonis format) |
| `string` | str | variable | Length-prefixed UTF-8 |
| `array_float32` | np.ndarray | variable | 1D float32 array |
| `array_float64` | np.ndarray | variable | 1D float64 array |
| `array_int32` | np.ndarray | variable | 1D int32 array |
| `array_string` | list[str] | variable | 1D string array |
| `matrix_float32` | np.ndarray | variable | 2D float32 matrix |

## Directory Structure

```
qcodes_nanonis/
├── src/nanonis/
│   ├── protocol/              # Layer 1: TCP Communication
│   │   ├── tcp_client.py      # NanonisTCPClient
│   │   └── exceptions.py      # Error hierarchy
│   ├── command/               # Layer 2: Command Interface
│   │   ├── controller.py      # NanonisController
│   │   ├── registry.py        # CommandRegistry
│   │   ├── encoder.py         # CommandEncoder/Decoder
│   │   └── proxies.py         # BiasProxy, ScanProxy, etc.
│   └── qcodes/                # Layer 3: QCoDeS Integration
│       ├── instrument.py      # NanonisInstrument
│       └── channels/          # BiasChannel, ScanChannel
├── nanonis_core/              # Optional Rust backend
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs             # PyO3 module exports
│       ├── client.rs          # Rust TCP client
│       ├── header.rs          # Protocol header
│       └── codec/             # Type encoders/decoders
├── configs/
│   ├── nanonis_tcp.yaml       # SPM commands (148)
│   └── nanonis_tramea.yaml    # TRAMEA commands (206)
├── tests/
├── doc/
│   ├── project_evaluation.md  # Technical evaluation
│   └── rust_refactor_review.md
└── pyproject.toml
```

## Performance

The optional Rust backend provides significant speedups for encoding/decoding:

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| encode_float32 | ~1.0 us | ~0.1 us | ~10x |
| encode_array (1000 floats) | ~100 us | ~5 us | ~20x |
| decode_matrix (100x100) | ~2 ms | ~0.05 ms | ~40x |

Check backend status:

```python
from nanonis.command.encoder import RUST_BACKEND
print(f"Rust backend: {'enabled' if RUST_BACKEND else 'disabled'}")
```

## Error Handling

```python
from nanonis.protocol.exceptions import (
    NanonisError,           # Base exception
    NanonisConnectionError, # Connection/socket failures
    NanonisProtocolError,   # Malformed responses
    NanonisTimeoutError,    # Socket timeouts
    NanonisCommandError,    # Nanonis device errors
)

try:
    with NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml') as ctrl:
        ctrl.send('Bias.Set', 0.5)
except NanonisConnectionError as e:
    print(f"Connection failed: {e}")
except NanonisTimeoutError as e:
    print(f"Operation timed out: {e}")
except NanonisCommandError as e:
    print(f"Nanonis returned error: {e}")
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=nanonis --cov-report=html

# Run only fast unit tests
pytest tests/ -v -m "not slow"
```

## Troubleshooting

### Connection Refused
- Verify Nanonis TCP server is enabled in software settings
- Check firewall allows connections on port 6501
- Confirm IP address and port are correct

### Timeout Errors
- Increase timeout for long operations: `ctrl = NanonisController(..., timeout=60.0)`
- Some operations (approach, retract) may take extended time

### Type Mismatch Errors
- Enable debug mode to see type coercion: `ctrl.debug = True`
- Check command definition in YAML matches hardware version

### Rust Backend Not Found
- Verify maturin build completed successfully
- Check Python version matches build target (3.9+)
- Try reinstalling: `cd nanonis_core && maturin develop --release`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/ -v`
4. Run linting: `ruff check src/`
5. Submit a pull request

## License

MIT License

## References

- [Nanonis TCP Protocol Documentation](doc/TCPProtocol_SPM.pdf)
- [QCoDeS Documentation](https://qcodes.github.io/Qcodes/)
- [nanonis_tramea](https://pypi.org/project/nanonis-tramea/)
- [PyO3 Documentation](https://pyo3.rs/)
