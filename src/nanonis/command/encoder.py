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
        'bool': ('>I', 4, np.uint32),  # Nanonis uses 4-byte bool
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
        
        This is critical for Nanonis which expects exact binary representations.
        For example, a Python float (64-bit) sent as float32 needs explicit conversion.
        """
        if dtype not in self.SCALAR_FORMATS:
            return value
        
        _, _, np_type = self.SCALAR_FORMATS[dtype]
        
        # Already correct type
        if isinstance(value, np_type):
            return value
        
        # Coerce to correct numpy type
        try:
            coerced = np_type(value)
            if self.debug:
                logger.debug(f"Coerced {type(value).__name__}({value}) -> {dtype}({coerced})")
            return coerced
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
                # Apply type coercion before encoding
                coerced_value = self._coerce_type(dtype, value)
                encoded = self._encode_value(dtype, coerced_value)
                result += encoded
                
                if self.debug:
                    logger.debug(f"Encoded {name}: {value} -> {len(encoded)} bytes")
            except Exception as e:
                raise ValueError(f"Failed to encode '{name}' as {dtype}: {e}") from e
        return result
    
    def _encode_value(self, dtype: str, value: Any) -> bytes:
        """Encode a single value based on its type."""
        
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
        """Encode a 1D array."""
        elem_type = dtype.replace('array_', '')
        
        if elem_type == 'string':
            # Array of strings: size + each string
            strings = list(value) if not isinstance(value, list) else value
            result = struct.pack('>I', len(strings))
            for s in strings:
                encoded = s.encode('utf-8') if isinstance(s, str) else s
                result += struct.pack('>I', len(encoded)) + encoded
            return result
        else:
            # Numeric array - force correct dtype
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            arr = np.asarray(value, dtype=np_dtype)
            return struct.pack('>I', len(arr)) + arr.tobytes()
    
    def _encode_2d_array(self, dtype: str, value: Any) -> bytes:
        """Encode a 2D array (matrix)."""
        elem_type = dtype.replace('matrix_', '')
        
        if elem_type == 'string':
            # 2D array of strings: rows + cols + each string
            matrix = list(value)
            rows = len(matrix)
            cols = len(matrix[0]) if rows > 0 else 0
            result = struct.pack('>II', rows, cols)
            for row in matrix:
                for s in row:
                    encoded = s.encode('utf-8') if isinstance(s, str) else s
                    result += struct.pack('>I', len(encoded)) + encoded
            return result
        else:
            # Numeric 2D array
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            arr = np.asarray(value, dtype=np_dtype)
            rows, cols = arr.shape
            return struct.pack('>II', rows, cols) + arr.tobytes()


class CommandDecoder:
    """
    Decodes bytes to Python values from Nanonis protocol.
    
    Features:
    - Automatic error detection and parsing from response
    - Debug logging support
    """
    
    SCALAR_FORMATS = {k: (v[0], v[1]) for k, v in CommandEncoder.SCALAR_FORMATS.items()}
    NUMPY_DTYPES = CommandEncoder.NUMPY_DTYPES
    
    def __init__(self, debug: bool = False):
        """
        Initialize decoder.
        
        Args:
            debug: Enable debug logging
        """
        self.debug = debug
    
    def decode(
        self, 
        args: List[Tuple[str, str]], 
        data: bytes,
        check_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Decode bytes according to type definitions.
        
        Args:
            args: List of (name, type) tuples
            data: Bytes to decode
            check_error: Whether to check for Nanonis error at end of response
            
        Returns:
            Dictionary mapping argument names to decoded values
            
        Raises:
            NanonisCommandError: If Nanonis returned an error
        """
        result = {}
        offset = 0
        
        for name, dtype in args:
            try:
                value, consumed = self._decode_value(dtype, data[offset:])
                result[name] = value
                offset += consumed
                
                if self.debug:
                    logger.debug(f"Decoded {name}: {consumed} bytes -> {type(value).__name__}")
            except Exception as e:
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
        
        Nanonis error format:
        - 4 bytes: error status (uint32, 0 = no error)
        - 4 bytes: error string length (uint32)
        - N bytes: error string (UTF-8)
        """
        if len(data) < 8:
            return None
        
        error_status = struct.unpack('>I', data[:4])[0]
        if error_status == 0:
            return None
        
        error_length = struct.unpack('>I', data[4:8])[0]
        if error_length > 0 and len(data) >= 8 + error_length:
            error_string = data[8:8 + error_length].decode('utf-8', errors='replace')
            if self.debug:
                logger.warning(f"Nanonis error: {error_string}")
            return error_string
        
        return f"Unknown error (status={error_status})"
    
    def _decode_value(self, dtype: str, data: bytes) -> Tuple[Any, int]:
        """
        Decode a single value from bytes.
        
        Returns:
            Tuple of (decoded_value, bytes_consumed)
        """
        # Handle scalar types
        if dtype in self.SCALAR_FORMATS:
            fmt, size = self.SCALAR_FORMATS[dtype]
            value = struct.unpack(fmt, data[:size])[0]
            if dtype == 'bool':
                value = bool(value)
            return value, size
        
        # Handle string
        if dtype == 'string':
            length = struct.unpack('>I', data[:4])[0]
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
        """Decode a 1D array."""
        elem_type = dtype.replace('array_', '')
        size = struct.unpack('>I', data[:4])[0]
        offset = 4
        
        if elem_type == 'string':
            # Array of strings
            strings = []
            for _ in range(size):
                str_len = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4
                strings.append(data[offset:offset+str_len].decode('utf-8'))
                offset += str_len
            return strings, offset
        else:
            # Numeric array
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            elem_size = np.dtype(np_dtype).itemsize
            arr_data = data[4:4 + size * elem_size]
            arr = np.frombuffer(arr_data, dtype=np_dtype).copy()
            return arr, 4 + size * elem_size
    
    def _decode_2d_array(self, dtype: str, data: bytes) -> Tuple[Any, int]:
        """Decode a 2D array (matrix)."""
        elem_type = dtype.replace('matrix_', '')
        rows = struct.unpack('>I', data[:4])[0]
        cols = struct.unpack('>I', data[4:8])[0]
        offset = 8
        
        if elem_type == 'string':
            # 2D array of strings
            matrix = []
            for _ in range(rows):
                row = []
                for _ in range(cols):
                    str_len = struct.unpack('>I', data[offset:offset+4])[0]
                    offset += 4
                    row.append(data[offset:offset+str_len].decode('utf-8'))
                    offset += str_len
                matrix.append(row)
            return matrix, offset
        else:
            # Numeric 2D array
            np_dtype = self.NUMPY_DTYPES.get(elem_type, f'>{elem_type[0]}4')
            elem_size = np.dtype(np_dtype).itemsize
            arr_data = data[8:8 + rows * cols * elem_size]
            arr = np.frombuffer(arr_data, dtype=np_dtype).reshape(rows, cols).copy()
            return arr, 8 + rows * cols * elem_size
