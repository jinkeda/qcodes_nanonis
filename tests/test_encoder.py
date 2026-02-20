# -*- coding: utf-8 -*-
"""
Tests for Encoder/Decoder

Tests for CommandEncoder and CommandDecoder roundtrip encoding.
"""

import struct
import pytest
import numpy as np

from nanonis.command.encoder import CommandEncoder, CommandDecoder


class TestCommandEncoder:
    """Tests for CommandEncoder."""
    
    def setup_method(self):
        self.encoder = CommandEncoder()
        self.decoder = CommandDecoder()
    
    def test_encode_float32(self):
        """Test float32 encoding."""
        args = [('value', 'float32')]
        encoded = self.encoder.encode(args, (1.5,))
        
        # Decode and verify
        result = self.decoder.decode(args, encoded)
        assert abs(result['value'] - 1.5) < 1e-6
    
    def test_encode_float64(self):
        """Test float64 encoding."""
        args = [('value', 'float64')]
        encoded = self.encoder.encode(args, (3.14159265358979,))
        
        result = self.decoder.decode(args, encoded)
        assert abs(result['value'] - 3.14159265358979) < 1e-14
    
    def test_encode_int32(self):
        """Test int32 encoding."""
        args = [('value', 'int32')]
        encoded = self.encoder.encode(args, (42,))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == 42
    
    def test_encode_negative_int32(self):
        """Test negative int32 encoding."""
        args = [('value', 'int32')]
        encoded = self.encoder.encode(args, (-100,))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == -100
    
    def test_encode_uint16(self):
        """Test uint16 encoding."""
        args = [('value', 'uint16')]
        encoded = self.encoder.encode(args, (1000,))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == 1000
    
    def test_encode_uint32(self):
        """Test uint32 encoding."""
        args = [('value', 'uint32')]
        encoded = self.encoder.encode(args, (100000,))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == 100000
    
    def test_encode_bool_true(self):
        """Test bool encoding (True) uses 4-byte big-endian format."""
        args = [('value', 'bool')]
        encoded = self.encoder.encode(args, (True,))
        assert encoded == struct.pack('>I', 1)
        result = self.decoder.decode(args, encoded)
        assert result['value'] is True
    
    def test_encode_bool_false(self):
        """Test bool encoding (False) uses 4-byte big-endian format."""
        args = [('value', 'bool')]
        encoded = self.encoder.encode(args, (False,))
        assert encoded == struct.pack('>I', 0)
        result = self.decoder.decode(args, encoded)
        assert result['value'] is False
    
    def test_encode_string(self):
        """Test string encoding."""
        args = [('value', 'string')]
        encoded = self.encoder.encode(args, ('Hello World',))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == 'Hello World'
    
    def test_encode_empty_string(self):
        """Test empty string encoding."""
        args = [('value', 'string')]
        encoded = self.encoder.encode(args, ('',))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == ''
    
    def test_encode_unicode_string(self):
        """Test unicode string encoding."""
        args = [('value', 'string')]
        encoded = self.encoder.encode(args, ('日本語',))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] == '日本語'
    
    def test_encode_array_float32(self):
        """Test float32 array encoding."""
        args = [('values', 'array_float32')]
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        encoded = self.encoder.encode(args, (arr,))
        
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_almost_equal(result['values'], arr)
    
    def test_encode_array_int32(self):
        """Test int32 array encoding."""
        args = [('values', 'array_int32')]
        arr = np.array([1, 2, 3, 4, 5], dtype=np.int32)
        encoded = self.encoder.encode(args, (arr,))
        
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_equal(result['values'], arr)
    
    def test_encode_array_string(self):
        """Test string array encoding."""
        args = [('values', 'array_string')]
        strings = ['hello', 'world', 'test']
        encoded = self.encoder.encode(args, (strings,))
        
        result = self.decoder.decode(args, encoded)
        assert result['values'] == strings

    def test_encode_empty_array_float32(self):
        """Test empty float32 array encoding."""
        args = [('values', 'array_float32')]
        arr = np.array([], dtype=np.float32)
        encoded = self.encoder.encode(args, (arr,))

        result = self.decoder.decode(args, encoded)
        assert result['values'].size == 0

    def test_encode_empty_array_int32(self):
        """Test empty int32 array encoding."""
        args = [('values', 'array_int32')]
        arr = np.array([], dtype=np.int32)
        encoded = self.encoder.encode(args, (arr,))

        result = self.decoder.decode(args, encoded)
        assert result['values'].size == 0

    def test_encode_empty_array_string(self):
        """Test empty string array encoding."""
        args = [('values', 'array_string')]
        encoded = self.encoder.encode(args, ([],))

        result = self.decoder.decode(args, encoded)
        assert result['values'] == []
    
    def test_encode_matrix_float32(self):
        """Test float32 2D array encoding."""
        args = [('values', 'matrix_float32')]
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        encoded = self.encoder.encode(args, (arr,))
        
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_almost_equal(result['values'], arr)
    
    def test_encode_matrix_string(self):
        """Test string 2D array encoding is not supported."""
        args = [('values', 'matrix_string')]
        matrix = [['a', 'b'], ['c', 'd']]
        with pytest.raises(ValueError, match='matrix_string encoding is not supported'):
            self.encoder.encode(args, (matrix,))
    
    def test_encode_multiple_args(self):
        """Test encoding multiple arguments."""
        args = [
            ('x', 'float64'),
            ('y', 'float64'),
            ('name', 'string'),
            ('count', 'int32'),
        ]
        values = (1.5, 2.5, 'test', 10)
        encoded = self.encoder.encode(args, values)
        
        result = self.decoder.decode(args, encoded)
        assert abs(result['x'] - 1.5) < 1e-14
        assert abs(result['y'] - 2.5) < 1e-14
        assert result['name'] == 'test'
        assert result['count'] == 10
    
    def test_encode_arg_count_mismatch(self):
        """Test error on argument count mismatch."""
        args = [('x', 'float32'), ('y', 'float32')]
        with pytest.raises(ValueError, match='Argument count mismatch'):
            self.encoder.encode(args, (1.0,))
    
    def test_encode_unknown_type(self):
        """Test error on unknown type."""
        args = [('value', 'unknown_type')]
        with pytest.raises(ValueError, match='Unknown type'):
            self.encoder.encode(args, ('test',))

    def test_encode_int32_boundaries(self):
        """Test int32 boundary values."""
        args = [('value', 'int32')]
        for value in (np.iinfo(np.int32).min, np.iinfo(np.int32).max):
            encoded = self.encoder.encode(args, (value,))
            result = self.decoder.decode(args, encoded)
            assert result['value'] == value

    def test_encode_uint32_max(self):
        """Test uint32 max value."""
        args = [('value', 'uint32')]
        value = np.iinfo(np.uint32).max
        encoded = self.encoder.encode(args, (value,))
        result = self.decoder.decode(args, encoded)
        assert result['value'] == value


class TestRoundtrip:
    """Roundtrip encoding/decoding tests."""
    
    def setup_method(self):
        self.encoder = CommandEncoder()
        self.decoder = CommandDecoder()
    
    def test_scan_frame_roundtrip(self):
        """Test Scan.FrameSet argument roundtrip."""
        args = [
            ('center_x', 'float64'),
            ('center_y', 'float64'),
            ('width', 'float64'),
            ('height', 'float64'),
            ('angle', 'float32'),
        ]
        values = (0.0, 0.0, 100e-9, 100e-9, 45.0)
        
        encoded = self.encoder.encode(args, values)
        result = self.decoder.decode(args, encoded)
        
        assert abs(result['center_x']) < 1e-15
        assert abs(result['center_y']) < 1e-15
        assert abs(result['width'] - 100e-9) < 1e-20
        assert abs(result['height'] - 100e-9) < 1e-20
        assert abs(result['angle'] - 45.0) < 1e-5
    
    def test_complex_command_roundtrip(self):
        """Test complex command with mixed types."""
        args = [
            ('enabled', 'bool'),
            ('setpoint', 'float32'),
            ('channels', 'array_int32'),
            ('name', 'string'),
        ]
        values = (True, 1e-10, np.array([0, 1, 2]), 'Current')
        
        encoded = self.encoder.encode(args, values)
        result = self.decoder.decode(args, encoded)
        
        assert result['enabled'] is True
        assert abs(result['setpoint'] - np.float32(1e-10)) < 1e-12
        np.testing.assert_array_equal(result['channels'], [0, 1, 2])
        assert result['name'] == 'Current'


class TestDecoderEdgeCases:
    """Decoder edge case tests."""

    def setup_method(self):
        self.decoder = CommandDecoder()

    def test_decode_string_truncated(self):
        args = [('value', 'string')]
        data = struct.pack('>I', 4) + b'a'
        with pytest.raises(ValueError, match='Not enough'):
            self.decoder.decode(args, data)

    def test_decode_array_string_truncated(self):
        args = [('values', 'array_string')]
        data = struct.pack('>I', 1) + struct.pack('>I', 5) + b'hi'
        with pytest.raises(ValueError, match='Not enough'):
            self.decoder.decode(args, data)

    def test_decode_matrix_truncated(self):
        args = [('values', 'matrix_float32')]
        data = struct.pack('>II', 2, 2) + b'\x00\x00\x00\x00'
        with pytest.raises(ValueError, match='Not enough'):
            self.decoder.decode(args, data)


class TestEdgeCases:
    """Edge case tests for encoder/decoder."""

    def setup_method(self):
        self.encoder = CommandEncoder()
        self.decoder = CommandDecoder()

    def test_float32_nan(self):
        """Test NaN encoding/decoding."""
        args = [('value', 'float32')]
        encoded = self.encoder.encode(args, (float('nan'),))
        result = self.decoder.decode(args, encoded)
        assert np.isnan(result['value'])

    def test_float32_positive_inf(self):
        """Test positive infinity encoding/decoding."""
        args = [('value', 'float32')]
        encoded = self.encoder.encode(args, (float('inf'),))
        result = self.decoder.decode(args, encoded)
        assert np.isinf(result['value']) and result['value'] > 0

    def test_float32_negative_inf(self):
        """Test negative infinity encoding/decoding."""
        args = [('value', 'float32')]
        encoded = self.encoder.encode(args, (float('-inf'),))
        result = self.decoder.decode(args, encoded)
        assert np.isinf(result['value']) and result['value'] < 0

    def test_float64_special_values(self):
        """Test float64 special values roundtrip."""
        args = [('value', 'float64')]
        for value in [float('nan'), float('inf'), float('-inf')]:
            encoded = self.encoder.encode(args, (value,))
            result = self.decoder.decode(args, encoded)
            if np.isnan(value):
                assert np.isnan(result['value'])
            else:
                assert result['value'] == value

    def test_string_with_null_bytes(self):
        """Test string containing null bytes."""
        args = [('value', 'string')]
        value = "hello\x00world"
        encoded = self.encoder.encode(args, (value,))
        result = self.decoder.decode(args, encoded)
        assert result['value'] == value

    def test_large_array_float32(self):
        """Test large array encoding (stress test)."""
        args = [('values', 'array_float32')]
        # 100k elements (smaller than 1M for faster tests)
        arr = np.random.randn(100_000).astype(np.float32)
        encoded = self.encoder.encode(args, (arr,))
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_almost_equal(result['values'], arr)

    def test_large_array_int32(self):
        """Test large int32 array encoding."""
        args = [('values', 'array_int32')]
        arr = np.arange(100_000, dtype=np.int32)
        encoded = self.encoder.encode(args, (arr,))
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_equal(result['values'], arr)

