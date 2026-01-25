# Rust/PyO3 Refactoring Plan Review

**Date**: 2026-01-25
**Reviewer**: Claude (AI Assistant)
**Status**: Reviewed with recommendations

---

## Overall Assessment: Well-Designed Plan

The plan is technically sound and well-thought-out. The layered approach and the decision to keep the Python API intact while replacing the low-level implementation is the right strategy.

---

## Decision Reviews

### Decision 1: Sync vs Async TCP — Agree with Option A

The recommendation to start with `std::net::TcpStream` is correct. The Nanonis protocol is fundamentally request-response — you send a command and wait for the result. Async would add complexity without meaningful benefit since:

1. The current Python code is synchronous
2. Nanonis hardware likely can't handle concurrent commands anyway
3. You can always add async later with `tokio` if needed

**Suggestion**: Consider using `BufReader`/`BufWriter` for the socket to reduce syscall overhead:

```rust
use std::io::{BufReader, BufWriter};
struct NanonisTcpClient {
    reader: Option<BufReader<TcpStream>>,
    writer: Option<BufWriter<TcpStream>>,
    // ...
}
```

### Decision 2: Package Structure — Recommend Option A (separate package)

**Disagree** with the original recommendation of Option B. A separate `nanonis-core` crate offers significant advantages:

| Aspect | Option A (Separate) | Option B (Bundled) |
|--------|---------------------|-------------------|
| **CI/CD** | Rust tests run independently | Must run full Python test suite |
| **Versioning** | Can version independently | Tied to Python package version |
| **Build caching** | Cached across projects | Rebuilt with every change |
| **Distribution** | PyPI + crates.io | PyPI only |
| **Reusability** | Other Rust projects can use it | Python-only |

**Recommended structure**:
```
qcodes_Nanonis/
├── nanonis_core/          # Separate Rust crate
│   ├── Cargo.toml
│   └── src/
├── src/nanonis/           # Python package
│   └── ...
└── pyproject.toml         # References nanonis_core as build dependency
```

You can use `maturin develop` for local development and publish to PyPI as a single wheel that includes the compiled Rust.

---

## Technical Feedback

### 1. Protocol Layer — Good, with suggestions

The proposed API matches the current Python implementation well:

```rust
fn send_raw(&mut self, command: &str, body: &[u8]) -> PyResult<Vec<u8>>
```

**Suggestions**:

1. **Return `Py<PyBytes>` instead of `Vec<u8>`** to avoid an extra copy:
```rust
fn send_raw(&mut self, py: Python<'_>, command: &str, body: &[u8]) -> PyResult<Py<PyBytes>> {
    let response = self.internal_send_raw(command, body)?;
    Ok(PyBytes::new(py, &response).into())
}
```

2. **Add a `with_timeout` method** for per-command timeouts (useful for long operations like approach):
```rust
fn send_raw_with_timeout(&mut self, command: &str, body: &[u8], timeout_secs: f64) -> PyResult<Vec<u8>>
```

3. **Header encoding should be `const` or at least compile-time verified**:
```rust
const HEADER_SIZE: usize = 40;
const COMMAND_NAME_SIZE: usize = 32;

fn encode_header(command: &str, body_size: usize) -> [u8; HEADER_SIZE] {
    let mut header = [0u8; HEADER_SIZE];
    // ...
}
```

### 2. Type System — Reconsider the enum approach

The `NanonisValue` enum is well-designed, but consider a different approach for PyO3:

**Current plan** (enum-based):
```rust
pub enum NanonisValue {
    Float32(f32),
    Float64(f64),
    // ...
}
```

**Alternative** (trait-based, more idiomatic for PyO3):
```rust
// Separate encode/decode functions per type
#[pyfunction]
fn encode_float32(value: f32) -> Vec<u8> { ... }

#[pyfunction]
fn decode_float32(data: &[u8]) -> PyResult<f32> { ... }

// Or a generic approach with type hints
#[pyfunction]
fn encode_value(py: Python, type_name: &str, value: PyObject) -> PyResult<Vec<u8>> { ... }
```

**Reason**: The enum approach requires converting between Python types and the Rust enum, then from the enum to bytes. This adds overhead. Direct per-type functions are simpler and faster.

### 3. NumPy Integration — Critical, handle carefully

The plan mentions `pyo3-numpy` which is correct, but be aware of these gotchas:

```rust
// GOOD: Zero-copy view (array must stay alive)
fn decode_array_float32<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let vec: Vec<f32> = decode_vec(data)?;
    Ok(PyArray1::from_vec(py, vec))
}

// CAUTION: For 2D arrays, consider row-major vs column-major
fn decode_matrix_float32<'py>(
    py: Python<'py>,
    data: &[u8],
    rows: usize,
    cols: usize
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    // Nanonis uses row-major (C-order), which matches NumPy default
    let vec: Vec<f32> = decode_vec(data)?;
    Ok(PyArray2::from_vec(py, (rows, cols), vec)?)
}
```

### 4. Missing from the plan: Error Types

The plan mentions `thiserror` but doesn't detail the error hierarchy. Suggested implementation matching the Python exceptions:

```rust
// src/errors.rs
use pyo3::exceptions::{PyConnectionError, PyTimeoutError, PyValueError};
use pyo3::prelude::*;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum NanonisError {
    #[error("Connection failed: {0}")]
    Connection(String),

    #[error("Protocol error: {0}")]
    Protocol(String),

    #[error("Timeout after {0} seconds")]
    Timeout(f64),

    #[error("Command error: {0}")]
    Command(String),

    #[error("Encoding error: {0}")]
    Encoding(String),
}

impl From<NanonisError> for PyErr {
    fn from(err: NanonisError) -> PyErr {
        match err {
            NanonisError::Connection(msg) => PyConnectionError::new_err(msg),
            NanonisError::Timeout(secs) => PyTimeoutError::new_err(format!("Timeout after {} seconds", secs)),
            NanonisError::Protocol(msg) | NanonisError::Command(msg) => PyValueError::new_err(msg),
            NanonisError::Encoding(msg) => PyValueError::new_err(msg),
        }
    }
}
```

### 5. Cargo.toml — Mostly good, some additions

```toml
[package]
name = "nanonis_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "nanonis_core"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }  # Update to 0.23
numpy = "0.23"                    # Updated name (was pyo3-numpy)
thiserror = "2.0"                 # Updated to 2.0
byteorder = "1.5"

# Consider adding:
bytes = "1.5"                     # Efficient byte buffer handling
smallvec = "1.13"                 # Stack-allocated vectors for small arrays

# Remove serde/serde_yaml - keep config loading in Python
# The Rust layer should just do encoding/decoding

[dev-dependencies]
pretty_assertions = "1.4"
proptest = "1.4"                  # Property-based testing for encoders
```

**Important**: Remove `serde_yaml` from Rust dependencies. The Python layer already handles YAML loading via `CommandRegistry`. The Rust layer should only receive the type information it needs as function arguments.

---

## Architecture Refinement

Based on analysis of the codebase, a slightly refined architecture is suggested:

```
┌─────────────────────────────────────────────────────────────┐
│ Python Layer (KEEP AS-IS)                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Layer 3: QCoDeS Instrument, Channels                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Layer 2: NanonisController, CommandRegistry, Proxies   │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Thin Python wrapper (adapter for Rust)                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ nanonis_core (Rust + PyO3)                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ TCP Client: connect, disconnect, send_raw               │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Codec: encode_*, decode_* for each type                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

The key insight: **Keep `CommandRegistry` and type dispatch in Python**. The Rust layer should be a "dumb" codec and TCP client. Python calls specific encode/decode functions based on the type information it already has.

---

## API Design Suggestion

Instead of:
```python
# Original proposed API
from nanonis_core import encode_args, decode_args
encoded = encode_args(args, values)  # Complex dispatch in Rust
```

Consider:
```python
# Simpler API - Python does the dispatch
from nanonis_core import (
    encode_float32, decode_float32,
    encode_float64, decode_float64,
    encode_string, decode_string,
    encode_array_float32, decode_array_float32,
    # ...
)

# In encoder.py
def encode(self, args, values):
    buffer = bytearray()
    for (name, dtype), value in zip(args, values):
        encoder_fn = self._encoders[dtype]  # Python dispatch
        buffer.extend(encoder_fn(value))    # Rust encoding
    return bytes(buffer)
```

This approach:
- Keeps dispatch logic in Python (easier to debug, modify)
- Rust functions are simple and focused
- Fewer cross-language boundaries per call (one call per value, not nested)

---

## Verification Plan Additions

The original verification plan is good. Additional suggestions:

### 1. Property-Based Testing (Rust)
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn roundtrip_float32(value: f32) {
        let encoded = encode_float32(value);
        let decoded = decode_float32(&encoded).unwrap();
        // Handle NaN specially
        if value.is_nan() {
            prop_assert!(decoded.is_nan());
        } else {
            prop_assert_eq!(decoded, value);
        }
    }
}
```

### 2. Compatibility Tests (Python)
```python
def test_rust_python_compatibility():
    """Ensure Rust produces identical bytes to Python."""
    test_cases = [
        ('float32', 1.5, b'\x3f\xc0\x00\x00'),
        ('float64', 1.5, b'\x3f\xf8\x00\x00\x00\x00\x00\x00'),
        ('int32', -42, b'\xff\xff\xff\xd6'),
        ('string', 'hello', b'\x00\x00\x00\x05hello'),
    ]
    for dtype, value, expected in test_cases:
        rust_result = getattr(nanonis_core, f'encode_{dtype}')(value)
        assert rust_result == expected, f"{dtype}: {rust_result} != {expected}"
```

### 3. Memory/Safety Tests
```python
def test_no_memory_leak():
    """Ensure repeated operations don't leak memory."""
    import tracemalloc
    tracemalloc.start()

    client = NanonisTcpClient('127.0.0.1', 6501, 10.0)
    for _ in range(10000):
        data = nanonis_core.encode_array_float32([1.0] * 1000)
        result = nanonis_core.decode_array_float32(data)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 100_000_000  # Less than 100MB peak
```

---

## Timeline Feedback

The 2-week estimate is **optimistic but achievable** if:

1. You're experienced with Rust and PyO3
2. You have a working Nanonis device for integration testing
3. No major blockers in maturin/wheel building for Windows

**More realistic estimate**:
- Phase 1 (setup): 1 day
- Phase 2 (TCP): 2-3 days
- Phase 3 (codecs): 4-5 days (11+ types × testing = more than expected)
- Phase 4 (integration): 3-4 days (Windows wheel building can be tricky)
- Phase 5 (migration): 2 days

**Total**: ~2.5-3 weeks

---

## Summary: Recommended Changes

| Original Plan | Recommendation |
|---------------|----------------|
| Option B (bundled package) | **Option A (separate crate)** for better CI/CD |
| `NanonisValue` enum | **Per-type functions** for simpler PyO3 interface |
| `encode_args(args, values)` | **`encode_float32(v)`, etc.** - dispatch in Python |
| Include `serde_yaml` in Rust | **Keep YAML loading in Python** |
| pyo3 0.22 | **pyo3 0.23** (latest stable) |
| 2 weeks | **2.5-3 weeks** more realistic |

The plan is solid. These are refinements, not fundamental issues.
