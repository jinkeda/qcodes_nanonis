# -*- coding: utf-8 -*-
"""
Tests for Encoder/Decoder

Tests for CommandEncoder and CommandDecoder roundtrip encoding.
"""

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
        """Test bool encoding (True)."""
        args = [('value', 'bool')]
        encoded = self.encoder.encode(args, (True,))
        
        result = self.decoder.decode(args, encoded)
        assert result['value'] is True
    
    def test_encode_bool_false(self):
        """Test bool encoding (False)."""
        args = [('value', 'bool')]
        encoded = self.encoder.encode(args, (False,))
        
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
    
    def test_encode_matrix_float32(self):
        """Test float32 2D array encoding."""
        args = [('values', 'matrix_float32')]
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        encoded = self.encoder.encode(args, (arr,))
        
        result = self.decoder.decode(args, encoded)
        np.testing.assert_array_almost_equal(result['values'], arr)
    
    def test_encode_matrix_string(self):
        """Test string 2D array encoding."""
        args = [('values', 'matrix_string')]
        matrix = [['a', 'b'], ['c', 'd']]
        encoded = self.encoder.encode(args, (matrix,))
        
        result = self.decoder.decode(args, encoded)
        assert result['values'] == matrix
    
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
        assert abs(result['setpoint'] - 1e-10) < 1e-16
        np.testing.assert_array_equal(result['channels'], [0, 1, 2])
        assert result['name'] == 'Current'
