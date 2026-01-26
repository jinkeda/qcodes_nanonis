# -*- coding: utf-8 -*-
"""
Command Encoder/Decoder

Handles encoding Python values to bytes and decoding bytes to Python values
based on the type definitions in the command registry.
"""

import struct
import logging
from typing import Any, Dict, List, Tuple, Optional
import numpy as np

from ..protocol.exceptions import NanonisCommandError

logger = logging.getLogger(__name__)

# Try to import Rust backend
try:
    import nanonis_core
    RUST_BACKEND = True
    logger.info("Using optimized Rust backend for Nanonis codec")
    
    # Map types to Rust functions
    RUST_ENCODERS = {
        'float32': nanonis_core.encode_float32,
        'float64': nanonis_core.encode_float64,
        'int16': nanonis_core.encode_int16,
        'int32': nanonis_core.encode_int32,
        'uint16': nanonis_core.encode_uint16,
        'uint32': nanonis_core.encode_uint32,
        'bool': nanonis_core.encode_bool,
        'string': nanonis_core.encode_string,
        
        # Arrays
        'array_float32': nanonis_core.encode_array_float32,
        'array_float64': nanonis_core.encode_array_float64,
        'array_int32': nanonis_core.encode_array_int32,
        'array_string': nanonis_core.encode_array_string,
        
        # Matrices
        'matrix_float32': nanonis_core.encode_matrix_float32,
    }
    
    RUST_DECODERS = {
        'float32': nanonis_core.decode_float32,
        'float64': nanonis_core.decode_float64,
        'int16': nanonis_core.decode_int16,
        'int32': nanonis_core.decode_int32,
        'uint16': nanonis_core.decode_uint16,
        'uint32': nanonis_core.decode_uint32,
        'bool': nanonis_core.decode_bool,
        'string': nanonis_core.decode_string,
        
        # Arrays
        'array_float32': nanonis_core.decode_array_float32,
        'array_float64': nanonis_core.decode_array_float64,
        'array_int32': nanonis_core.decode_array_int32,
        'array_string': nanonis_core.decode_array_string,
        
        # Matrices
        'matrix_float32': nanonis_core.decode_matrix_float32,
    }
    
except ImportError:
    RUST_BACKEND = False
    logger.warning("Rust backend not found, using slower Python implementation")


class CommandEncoder:
    """
    Encodes Python values to bytes for Nanonis protocol.
    
    Supports:
    - Scalar types: float32, float64, int16, int32, uint16, uint32, bool
    - String: length-prefixed UTF-8
    - 1D Arrays: array_float32, array_int32, array_string
    - 2D Arrays: matrix_float32, matrix_string
    
    Features:
    - Automatic type coercion to prevent precision loss
    - Debug logging support
    """
    
    # Scalar type formats (struct format, size, numpy dtype)
    SCALAR_FORMATS = {
        'float32': ('>f', 4, np.float32),
        'float64': ('>d', 8, np.float64),
        'int16': ('>h', 2, np.int16),
        'int32': ('>i', 4, np.int32),
        'uint16': ('>H', 2, np.uint16),
        'uint32': ('>I', 4, np.uint32),
        # NOTE: Nanonis uses 4-byte booleans (uint32), not 1-byte.
        # This is a protocol quirk - True = 0x00000001, False = 0x00000000.
        # The reason is unknown but may relate to memory alignment on the
        # Nanonis controller hardware.
        'bool': ('>I', 4, np.uint32),
    }
    
    # NumPy dtype mapping for arrays
    NUMPY_DTYPES = {
        'float32': '>f4',
        'float64': '>f8',
        'int32': '>i4',
        'uint16': '>u2',
        'uint32': '>u4',
    }
    
    def __init__(self, debug: bool = False):
        """
        Initialize encoder.
        
        Args:
            debug: Enable debug logging
        """
        self.debug = debug
    
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
        if dtype == 'bool':
            return bool(value)
        if dtype not in self.SCALAR_FORMATS:
            return value
        
        _, _, np_type = self.SCALAR_FORMATS[dtype]
        
        # Already correct type
        if isinstance(value, np_type):
            return value
        
        # Coerce to correct numpy type
        try:
            return np_type(value)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Cannot coerce {value} to {dtype}: {e}") from e
    
    def encode(self, args: List[Tuple[str, str]], values: tuple) -> bytes:
        """
        Encode multiple values according to their type definitions.
        
        Args:
            args: List of (name, type) tuples
            values: Tuple of values to encode
            
        Returns:
            Encoded bytes
        """
        if len(args) != len(values):
            raise ValueError(
                f"Argument count mismatch: expected {len(args)}, got {len(values)}"
            )
        
        result = b''
        for (name, dtype), value in zip(args, values):
            try:
                # Apply type coercion first
                coerced_value = self._coerce_type(dtype, value)
                
                # Use Rust backend if available and supported
                if RUST_BACKEND and dtype in RUST_ENCODERS:
                    encoder = RUST_ENCODERS[dtype]
                    
                    # Special handling for arrays/matrices - need lists/vecs
                    if dtype.startswith(('array_', 'matrix_')) and isinstance(coerced_value, np.ndarray):
                        encoded = encoder(coerced_value.tolist())
                    else:
                        encoded = encoder(coerced_value)
                        
                    # Rust returns bytearray/Vec<u8> (bytes)
                    result += bytes(encoded)
                else:
                    # Fallback to Python implementation
                    result += self._encode_value(dtype, coerced_value)
                
                if self.debug:
                    logger.debug(f"Encoded {name} ({dtype})")
            except Exception as e:
                raise ValueError(f"Failed to encode '{name}' as {dtype}: {e}") from e
        return result
    
    def _encode_value(self, dtype: str, value: Any) -> bytes:
        """Encode a single value (Python fallback)."""
        
        # Handle scalar types
        if dtype in self.SCALAR_FORMATS:
            fmt, _, _ = self.SCALAR_FORMATS[dtype]
            if dtype == 'bool':
                value = 1 if value else 0
            return struct.pack(fmt, value)
        
        # Handle string
        if dtype == 'string':
            encoded = value.encode('utf-8') if isinstance(value, str) else value
            return struct.pack('>I', len(encoded)) + encoded
        
        # Handle 1D arrays
        if dtype.startswith('array_'):
            return self._encode_1d_array(dtype, value)
        
        # Handle 2D arrays/matrices
        if dtype.startswith('matrix_'):
            return self._encode_2d_array(dtype, value)
        
        raise ValueError(f"Unknown type: {dtype}")
    
    def _encode_1d_array(self, dtype: str, value: Any) -> bytes:
        """Encode a 1D array (Python fallback)."""
        elem_type = dtype.replace('array_', '')
        
        if elem_type == 'string':
            strings = list(value) if not isinstance(value, list) else value
            result = struct.pack('>I', len(strings))
            for s in strings:
                encoded = s.encode('utf-8') if isinstance(s, str) else s
                result += struct.pack('>I', len(encoded)) + encoded
            return result
        else:
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            arr = np.asarray(value, dtype=np_dtype)
            return struct.pack('>I', len(arr)) + arr.tobytes()
    
    def _encode_2d_array(self, dtype: str, value: Any) -> bytes:
        """Encode a 2D array (Python fallback)."""
        elem_type = dtype.replace('matrix_', '')
        
        # matrix_string is not supported
        if elem_type == 'string':
            raise NotImplementedError(
                "matrix_string encoding is not supported. "
                "Use array_string for 1D string arrays or flatten your data."
            )
        
        # Only matrix_float32 is common
        np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
        arr = np.asarray(value, dtype=np_dtype)
        rows, cols = arr.shape
        return struct.pack('>II', rows, cols) + arr.tobytes()


class CommandDecoder:
    """
    Decodes bytes to Python values from Nanonis protocol.
    """
    
    SCALAR_FORMATS = {k: (v[0], v[1]) for k, v in CommandEncoder.SCALAR_FORMATS.items()}
    NUMPY_DTYPES = CommandEncoder.NUMPY_DTYPES
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def decode(
        self, 
        args: List[Tuple[str, str]], 
        data: bytes,
        check_error: bool = True,
    ) -> Dict[str, Any]:
        """Decode bytes according to type definitions."""
        result = {}
        offset = 0
        
        # Convert to bytes if needed (Rust needs &[u8])
        data_bytes = bytes(data) if not isinstance(data, bytes) else data
        
        for name, dtype in args:
            try:
                # Use Rust backend if available
                if RUST_BACKEND and dtype in RUST_DECODERS:
                    decoder = RUST_DECODERS[dtype]
                    
                    # Pass slice of remaining data
                    remaining = data_bytes[offset:]
                    
                    # Rust decoders return:
                    # - Scalars: value (we calculate size)
                    # - Strings: (value, consumed_bytes)
                    # - Arrays: NumPy array (we calculate size)
                    
                    decoded = decoder(remaining)
                    
                    if dtype == 'string':
                        # String decoder returns tuple (str, size)
                        value, size = decoded
                    elif dtype == 'bool':
                        # Bool decoder returns int, convert to Python bool
                        value = bool(decoded)
                        _, size = self.SCALAR_FORMATS[dtype]
                    elif dtype in self.SCALAR_FORMATS:
                        # Scalar decoder returns value only
                        value = decoded
                        _, size = self.SCALAR_FORMATS[dtype]
                    elif dtype.startswith('array_') and dtype != 'array_string':
                        # Numeric array decoder returns numpy array
                        value = decoded
                        # Calculate size: 4 (len) + elems * itemsize
                        size = 4 + value.size * value.itemsize
                    elif dtype == 'array_string':
                        # String array decoder returns list[str]
                        # Need to calculate consumed bytes... simpler to use Python for complex var-len arrays
                        # Or update Rust to return consumed bytes.
                        # For now, let's fallback for complex types if needed, 
                        # but decode_array_string returns Vec<String>.
                        # Calculating consumed size properly requires iterating strings.
                        # Let's fallback to Python for array_string to be safe on offset.
                        raise NotImplementedError("Rust array_string size calc TODO")
                    elif dtype.startswith('matrix_'):
                        value = decoded
                        # Matrix: 4 (rows) + 4 (cols) + elems * itemsize
                        size = 8 + value.size * value.itemsize
                    else:
                        # Fallback
                        raise NotImplementedError(f"Rust decoder size calc for {dtype}")
                        
                    result[name] = value
                    offset += size
                    
                else:
                    # Fallback to Python
                    value, consumed = self._decode_value(dtype, data[offset:])
                    result[name] = value
                    offset += consumed
                
                if self.debug:
                    logger.debug(f"Decoded {name} ({dtype})")
                    
            except (Exception, NotImplementedError) as e:
                # Retry with Python fallback immediately if Rust failed/skipped
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
                
                raise ValueError(f"Failed to decode '{name}' as {dtype}: {e}") from e
        
        # Check for error in remaining bytes
        if check_error and offset < len(data):
            error_info = self._parse_error(data[offset:])
            if error_info:
                raise NanonisCommandError("command", error_info)
        
        return result
    
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
        if len(data) < 8:
            return None
        
        error_status = struct.unpack('>I', data[:4])[0]
        if error_status == 0:
            return None
        
        error_length = struct.unpack('>I', data[4:8])[0]
        if error_length > 0 and len(data) >= 8 + error_length:
            return data[8:8 + error_length].decode('utf-8', errors='replace')
        
        return f"Unknown error (status={error_status})"
    
    def _decode_value(self, dtype: str, data: bytes) -> Tuple[Any, int]:
        """Decode a single value (Python fallback)."""
        # Handle scalar types
        if dtype in self.SCALAR_FORMATS:
            fmt, size = self.SCALAR_FORMATS[dtype]
            value = struct.unpack(fmt, data[:size])[0]
            if dtype == 'bool':
                value = bool(value)
            return value, size
        
        # Handle string
        if dtype == 'string':
            if len(data) < 4:
                raise ValueError("Not enough data for string length")
            length = struct.unpack('>I', data[:4])[0]
            if len(data) < 4 + length:
                raise ValueError("Not enough data for string body")
            string_data = data[4:4+length].decode('utf-8')
            return string_data, 4 + length
        
        # Handle 1D arrays
        if dtype.startswith('array_'):
            return self._decode_1d_array(dtype, data)
        
        # Handle 2D arrays/matrices
        if dtype.startswith('matrix_'):
            return self._decode_2d_array(dtype, data)
        
        raise ValueError(f"Unknown type: {dtype}")
    
    def _decode_1d_array(self, dtype: str, data: bytes) -> Tuple[Any, int]:
        """Decode a 1D array (Python fallback)."""
        elem_type = dtype.replace('array_', '')
        
        if len(data) < 4:
            raise ValueError("Not enough data for array length")
            
        size = struct.unpack('>I', data[:4])[0]
        offset = 4
        
        if elem_type == 'string':
            strings = []
            for _ in range(size):
                if len(data) < offset + 4:
                    raise ValueError("Not enough data for string length")
                str_len = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4
                if len(data) < offset + str_len:
                    raise ValueError("Not enough data for string body")
                strings.append(data[offset:offset+str_len].decode('utf-8'))
                offset += str_len
            return strings, offset
        else:
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            elem_size = np.dtype(np_dtype).itemsize
            expected = 4 + size * elem_size
            if len(data) < expected:
                raise ValueError("Not enough data for array values")
            arr_data = data[4:4 + size * elem_size]
            arr = np.frombuffer(arr_data, dtype=np_dtype).copy()
            return arr, expected
    
    def _decode_2d_array(self, dtype: str, data: bytes) -> Tuple[Any, int]:
        """Decode a 2D array (Python fallback)."""
        elem_type = dtype.replace('matrix_', '')
        
        if len(data) < 8:
            raise ValueError("Not enough data for matrix dimensions")
            
        rows = struct.unpack('>I', data[:4])[0]
        cols = struct.unpack('>I', data[4:8])[0]
        
        # Only matrix_float32 is typical
        np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
        elem_size = np.dtype(np_dtype).itemsize
        expected = 8 + rows * cols * elem_size
        
        if len(data) < expected:
            raise ValueError("Not enough data for matrix values")
        arr_data = data[8:expected]
        arr = np.frombuffer(arr_data, dtype=np_dtype).reshape(rows, cols).copy()
        return arr, expected
