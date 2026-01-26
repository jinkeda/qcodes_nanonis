# Refactoring Recommendations Report

**Project**: QCoDeS Nanonis
**Date**: 2026-01-26
**Evaluation Principles**: Reverse Engineering, Modernization, Documentation

---

## Executive Summary

This report identifies refactoring opportunities in the QCoDeS Nanonis codebase based on three principles:

1. **Reverse Engineering**: Trace logic in undocumented systems to understand intent
2. **Modernization**: Map legacy patterns to modern ones incrementally
3. **Documentation**: Leave the campground cleaner than you found it

The codebase is well-architected overall. Recommendations focus on incremental improvements rather than major rewrites.

---

## Table of Contents

1. [Critical Issues](#1-critical-issues)
2. [Documentation Gaps](#2-documentation-gaps)
3. [Code Quality Improvements](#3-code-quality-improvements)
4. [Modernization Opportunities](#4-modernization-opportunities)
5. [Testing Gaps](#5-testing-gaps)
6. [Protocol Documentation](#6-protocol-documentation)
7. [Implementation Checklist](#7-implementation-checklist)

---

## 1. Critical Issues

These items should be addressed before any release.

### 1.1 Rust Module Export Missing

**Location**: `nanonis_core/src/lib.rs:68` and `benchmarks/bench_codec.py:163`

**Problem**: The benchmark references `decode_string_simple` but it's not available at runtime despite being in the source code.

**Root Cause**: The Rust module needs to be rebuilt after the function was added.

**Fix**:
```bash
cd nanonis_core && maturin develop --release
```

**Priority**: High
**Effort**: 5 minutes

---

### 1.2 Silent Exception Swallowing in Decoder

**Location**: `src/nanonis/command/encoder.py:323-332`

**Current Code**:
```python
except (Exception, NotImplementedError) as e:
    if RUST_BACKEND and isinstance(e, NotImplementedError):
        try:
            value, consumed = self._decode_value(dtype, data[offset:])
            result[name] = value
            offset += consumed
            continue
        except Exception:
            pass  # <-- Silent failure masks real errors
```

**Problem**: The bare `except Exception: pass` swallows errors silently, making debugging difficult.

**Recommended Fix**:
```python
except (Exception, NotImplementedError) as e:
    if RUST_BACKEND and isinstance(e, NotImplementedError):
        try:
            value, consumed = self._decode_value(dtype, data[offset:])
            result[name] = value
            offset += consumed
            continue
        except Exception as fallback_error:
            logger.warning(
                f"Both Rust and Python decoding failed for {name} ({dtype}): "
                f"Rust: {e}, Python: {fallback_error}"
            )
            raise ValueError(
                f"Failed to decode '{name}' as {dtype}: {fallback_error}"
            ) from fallback_error
```

**Priority**: High
**Effort**: 15 minutes

---

### 1.3 Boolean Encoding Test Failures

**Location**: `tests/test_encoder.py:71-85`

**Problem**: Tests assert specific byte sequences for boolean encoding, but the Rust backend may produce different (but semantically equivalent) results.

**Analysis**: Both implementations encode `True` as `0x00000001` (4-byte big-endian), so this should pass. If tests fail, investigate whether:
- The Rust backend returns `bytearray` vs `bytes`
- There's a type coercion issue in the encoder

**Action**: Run tests with `RUST_BACKEND=False` to isolate the issue:
```bash
# Temporarily disable Rust to test Python-only path
import sys
sys.modules['nanonis_core'] = None
```

**Priority**: High
**Effort**: 1-2 hours to diagnose and fix

---

## 2. Documentation Gaps

### 2.1 Missing Protocol Magic Value Explanations

**Location**: `src/nanonis/protocol/tcp_client.py:196-198`

**Current Code**:
```python
# Flags: 4 bytes (send=1, reserved=0)
flags = struct.pack('>HH', 1, 0)
```

**Problem**: Why is send flag always 1? What do other values mean? This appears to be reverse-engineered but the discovery is not documented.

**Recommended Addition**:
```python
# Flags: 4 bytes total
# - Bytes 0-1: Send flag (uint16, big-endian)
#   - 1 = Request (client -> Nanonis)
#   - 0 = Response (Nanonis -> client, never set by us)
#   - Other values: Unknown/undocumented
# - Bytes 2-3: Reserved (uint16, always 0)
# Note: These values were determined by protocol analysis; official
# documentation may not exist.
flags = struct.pack('>HH', 1, 0)
```

**Priority**: Medium
**Effort**: 10 minutes

---

### 2.2 Type Coercion Rationale Undocumented

**Location**: `src/nanonis/command/encoder.py:114-133`

**Current Code**:
```python
def _coerce_type(self, dtype: str, value: Any) -> Any:
    """
    Coerce value to correct numpy type to prevent precision loss.
    """
```

**Problem**: The docstring says "prevent precision loss" but doesn't explain:
- When precision loss occurs
- Why numpy types are needed
- What happens if coercion fails

**Recommended Docstring**:
```python
def _coerce_type(self, dtype: str, value: Any) -> Any:
    """
    Coerce value to correct numpy type to prevent precision loss.

    The Nanonis protocol uses specific binary formats (e.g., IEEE 754 float32).
    Python's native float is 64-bit, so passing a Python float to struct.pack('>f', ...)
    may lose precision silently. By explicitly converting to np.float32 first,
    we ensure the user sees the actual value that will be transmitted.

    Example:
        >>> value = 0.1  # Python float64
        >>> np.float32(value)  # Shows actual transmitted value: 0.1000000014901161

    Args:
        dtype: Target type name (e.g., 'float32', 'int16')
        value: Input value to coerce

    Returns:
        Value converted to appropriate numpy type, or original if not a scalar type

    Raises:
        ValueError: If value cannot be coerced (e.g., overflow)
    """
```

**Priority**: Medium
**Effort**: 15 minutes

---

### 2.3 4-Byte Boolean Protocol Quirk

**Location**: `src/nanonis/command/encoder.py:93` and `nanonis_core/src/codec/scalars.rs:61-68`

**Problem**: Nanonis uses 4-byte booleans (uint32), which is unusual. This should be prominently documented.

**Recommended Addition** (encoder.py):
```python
SCALAR_FORMATS = {
    # ...
    # NOTE: Nanonis uses 4-byte booleans (uint32), not 1-byte.
    # This is a protocol quirk - True = 0x00000001, False = 0x00000000.
    # The reason is unknown but may relate to memory alignment on the
    # Nanonis controller hardware.
    'bool': ('>I', 4, np.uint32),
}
```

**Priority**: Medium
**Effort**: 5 minutes

---

### 2.4 Error Response Format

**Location**: `src/nanonis/command/encoder.py:344-357`

**Current Code**:
```python
def _parse_error(self, data: bytes) -> Optional[str]:
    """Parse error information from response tail."""
```

**Problem**: The error format was clearly reverse-engineered but the structure is not documented.

**Recommended Docstring**:
```python
def _parse_error(self, data: bytes) -> Optional[str]:
    """
    Parse error information from response tail.

    Nanonis appends error information after the normal response data.

    Error format (variable length):
        Bytes 0-3:   Error status (uint32, big-endian)
                     - 0 = Success (no error)
                     - Non-zero = Error code
        Bytes 4-7:   Error message length (uint32, big-endian)
        Bytes 8+:    UTF-8 encoded error message

    Args:
        data: Remaining bytes after decoding expected response fields

    Returns:
        Error message string if error detected, None otherwise
    """
```

**Priority**: Medium
**Effort**: 10 minutes

---

## 3. Code Quality Improvements

### 3.1 Reduce Code Duplication in Rust Backend Checks

**Location**: Multiple files (`encoder.py`, `tcp_client.py`)

**Current Pattern**:
```python
# In encoder.py
try:
    import nanonis_core
    RUST_BACKEND = True
except ImportError:
    RUST_BACKEND = False

# In tcp_client.py (duplicated)
try:
    import nanonis_core
    RUST_BACKEND = True
except ImportError:
    RUST_BACKEND = False
```

**Recommended Refactor**: Create a single backend detection module.

```python
# src/nanonis/_backend.py
"""
Backend detection for optional Rust acceleration.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import nanonis_core
    RUST_AVAILABLE = True
    logger.info("Rust backend available")
except ImportError:
    nanonis_core = None  # type: ignore
    RUST_AVAILABLE = False
    logger.debug("Rust backend not available, using pure Python")

def get_rust_module():
    """Get the Rust module or None if unavailable."""
    return nanonis_core if RUST_AVAILABLE else None
```

Then import from this module:
```python
# In encoder.py
from .._backend import RUST_AVAILABLE, get_rust_module
```

**Priority**: Low
**Effort**: 30 minutes

---

### 3.2 Use `__all__` for Public API

**Location**: `src/nanonis/__init__.py`, `src/nanonis/command/__init__.py`

**Problem**: No explicit `__all__` declaration makes the public API unclear.

**Recommended Addition**:
```python
# src/nanonis/__init__.py
__all__ = [
    "NanonisController",
    "NanonisTCPClient",
    "NanonisError",
    "NanonisConnectionError",
    "NanonisProtocolError",
    "NanonisTimeoutError",
    "NanonisCommandError",
]
```

**Priority**: Low
**Effort**: 15 minutes

---

### 3.3 Add `__slots__` to Data Classes

**Location**: `src/nanonis/command/registry.py`

**Problem**: `CommandDefinition` and `ArgDefinition` classes could benefit from `__slots__` for memory efficiency when loading 354 commands.

**Current**:
```python
class ArgDefinition:
    def __init__(self, name: str, type: str, original_name: str = ''):
        self.name = name
        self.type = type
        self.original_name = original_name
```

**Recommended**:
```python
class ArgDefinition:
    __slots__ = ('name', 'type', 'original_name')

    def __init__(self, name: str, type: str, original_name: str = ''):
        self.name = name
        self.type = type
        self.original_name = original_name
```

**Priority**: Low
**Effort**: 10 minutes

---

## 4. Modernization Opportunities

### 4.1 Consider `dataclasses` for Registry Types

**Location**: `src/nanonis/command/registry.py`

**Current**: Manual `__init__` methods.

**Modern Alternative**:
```python
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True, slots=True)
class ArgDefinition:
    name: str
    type: str
    original_name: str = ''

@dataclass(slots=True)
class CommandDefinition:
    name: str
    send_args: List[ArgDefinition] = field(default_factory=list)
    recv_args: List[ArgDefinition] = field(default_factory=list)

    def get_send_types(self) -> List[tuple[str, str]]:
        return [(a.name, a.type) for a in self.send_args]
```

**Benefits**:
- Automatic `__repr__`, `__eq__`
- `frozen=True` prevents accidental mutation
- `slots=True` for memory efficiency

**Priority**: Low (nice-to-have)
**Effort**: 1 hour

---

### 4.2 Use `pathlib` Consistently

**Location**: `src/nanonis/command/controller.py:98-109`

**Current**:
```python
def load_config(self, path: Union[str, Path]) -> None:
    path = Path(path)  # Converts str to Path
```

**Already Good**: The code accepts both `str` and `Path`, which is the recommended approach.

**No Change Needed**: This is already modern.

---

### 4.3 Consider Async Support (Future)

**Assessment**: The current synchronous design is appropriate for instrument control where:
- Operations are inherently sequential (set voltage, then measure)
- Blocking is expected behavior
- Simplicity aids debugging

**Recommendation**: Do NOT add async support unless there's a concrete use case requiring concurrent operations. Adding async would:
- Double the API surface
- Complicate error handling
- Provide minimal benefit for typical SPM workflows

**Priority**: Not recommended
**Effort**: N/A

---

## 5. Testing Gaps

### 5.1 No QCoDeS Integration Tests

**Location**: `tests/` (missing `test_qcodes_instrument.py` content)

**Problem**: Layer 3 (QCoDeS integration) has no test coverage.

**Recommended Tests**:
```python
# tests/test_qcodes_instrument.py
import pytest
from unittest.mock import Mock, patch

class TestNanonisInstrument:
    """Tests for QCoDeS NanonisInstrument."""

    @pytest.fixture
    def mock_controller(self):
        with patch('nanonis.qcodes.instrument.NanonisController') as mock:
            mock.return_value.is_connected = True
            yield mock.return_value

    def test_bias_voltage_get(self, mock_controller):
        """Test reading bias voltage through QCoDeS parameter."""
        mock_controller.send.return_value = 0.5

        from nanonis.qcodes import NanonisInstrument
        inst = NanonisInstrument('test', '127.0.0.1', 6501, 'config.yaml')

        voltage = inst.bias.voltage()

        mock_controller.send.assert_called_with('Bias.Get')
        assert voltage == 0.5

    def test_bias_voltage_set(self, mock_controller):
        """Test setting bias voltage through QCoDeS parameter."""
        from nanonis.qcodes import NanonisInstrument
        inst = NanonisInstrument('test', '127.0.0.1', 6501, 'config.yaml')

        inst.bias.voltage(0.5)

        mock_controller.send.assert_called_with('Bias.Set', 0.5)
```

**Priority**: High
**Effort**: 4-6 hours

---

### 5.2 Missing Edge Case Tests

**Location**: `tests/test_encoder.py`

**Missing Tests**:
```python
class TestEdgeCases:
    """Edge case tests for encoder/decoder."""

    def test_float32_special_values(self):
        """Test NaN, Inf, -Inf encoding."""
        encoder = CommandEncoder()
        decoder = CommandDecoder()
        args = [('value', 'float32')]

        for value in [float('nan'), float('inf'), float('-inf')]:
            encoded = encoder.encode(args, (value,))
            result = decoder.decode(args, encoded)
            if np.isnan(value):
                assert np.isnan(result['value'])
            else:
                assert result['value'] == value

    def test_string_with_null_bytes(self):
        """Test string containing null bytes."""
        encoder = CommandEncoder()
        decoder = CommandDecoder()
        args = [('value', 'string')]

        value = "hello\x00world"
        encoded = encoder.encode(args, (value,))
        result = decoder.decode(args, encoded)
        assert result['value'] == value

    def test_maximum_array_size(self):
        """Test large array encoding (stress test)."""
        encoder = CommandEncoder()
        decoder = CommandDecoder()
        args = [('values', 'array_float32')]

        # 1 million elements
        arr = np.zeros(1_000_000, dtype=np.float32)
        encoded = encoder.encode(args, (arr,))
        result = decoder.decode(args, encoded)
        assert result['values'].shape == arr.shape
```

**Priority**: Medium
**Effort**: 2-3 hours

---

### 5.3 Rust Property-Based Tests Underutilized

**Location**: `nanonis_core/src/codec/scalars.rs:205-247`

**Current**: Proptest is set up but only tests roundtrip consistency.

**Recommended Addition**:
```rust
proptest! {
    #[test]
    fn proptest_float32_matches_python(value in any::<f32>()) {
        // Verify Rust encoding matches Python struct.pack('>f', value)
        let encoded = encode_float32(value);

        // Known IEEE 754 big-endian format
        let expected = value.to_be_bytes();
        prop_assert_eq!(encoded.as_slice(), &expected);
    }

    #[test]
    fn proptest_bool_is_4_bytes(value in any::<bool>()) {
        let encoded = encode_bool(value);
        prop_assert_eq!(encoded.len(), 4);
        prop_assert!(encoded[0..3] == [0, 0, 0]);  // First 3 bytes always 0
    }
}
```

**Priority**: Medium
**Effort**: 2 hours

---

## 6. Protocol Documentation

### 6.1 Add Protocol Specification to README

**Recommended Section**:

```markdown
## Protocol Specification

The Nanonis TCP protocol uses a simple request-response pattern over TCP.

### Message Format

```
+----------------+----------------+----------------+
|    Header      |      Body      |   (Response)   |
|   (40 bytes)   | (variable len) |  Error Info    |
+----------------+----------------+----------------+
```

### Header Format (40 bytes)

| Offset | Size | Type   | Description                    |
|--------|------|--------|--------------------------------|
| 0      | 32   | ASCII  | Command name (null-padded)     |
| 32     | 4    | int32  | Body size (big-endian)         |
| 36     | 2    | uint16 | Send flag (1=request, 0=response) |
| 38     | 2    | uint16 | Reserved (always 0)            |

### Data Types

| Type          | Size    | Format              |
|---------------|---------|---------------------|
| float32       | 4 bytes | IEEE 754, big-endian |
| float64       | 8 bytes | IEEE 754, big-endian |
| int16/uint16  | 2 bytes | Two's complement, big-endian |
| int32/uint32  | 4 bytes | Two's complement, big-endian |
| bool          | 4 bytes | uint32 (0=false, 1=true) |
| string        | 4+N     | uint32 length + UTF-8 bytes |
| array_T       | 4+N*S   | uint32 count + elements |
| matrix_T      | 8+R*C*S | uint32 rows, cols + elements |
```

**Priority**: Medium
**Effort**: 30 minutes

---

## 7. Implementation Checklist

### High Priority (Before Release)

- [ ] Rebuild Rust module: `cd nanonis_core && maturin develop --release`
- [ ] Fix silent exception swallowing in `encoder.py:323-332`
- [ ] Investigate and fix boolean encoding test failures
- [ ] Add QCoDeS integration tests

### Medium Priority (Beta Phase)

- [ ] Add protocol magic value documentation (`tcp_client.py`)
- [ ] Document type coercion rationale (`encoder.py`)
- [ ] Document 4-byte boolean quirk
- [ ] Document error response format
- [ ] Add protocol specification to README
- [ ] Add edge case tests (NaN, Inf, null bytes, large arrays)
- [ ] Expand Rust property-based tests

### Low Priority (Future)

- [ ] Consolidate Rust backend detection into `_backend.py`
- [ ] Add `__all__` declarations
- [ ] Add `__slots__` to data classes
- [ ] Consider `dataclasses` for registry types

---

## Appendix: Files to Modify

| File | Changes Needed |
|------|----------------|
| `src/nanonis/command/encoder.py` | Fix exception handling, add docstrings |
| `src/nanonis/protocol/tcp_client.py` | Add protocol documentation comments |
| `nanonis_core/src/codec/scalars.rs` | Expand proptest coverage |
| `tests/test_encoder.py` | Add edge case tests |
| `tests/test_qcodes_instrument.py` | Create QCoDeS tests |
| `README.md` | Add protocol specification section |

---

*Report generated based on codebase analysis following Reverse Engineering, Modernization, and Documentation principles.*
