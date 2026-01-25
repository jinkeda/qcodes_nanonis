//! Scalar type encoders and decoders
//!
//! All values use big-endian byte order as per Nanonis protocol.

use crate::errors::NanonisError;
use pyo3::prelude::*;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

// ============================================================================
// ENCODERS
// ============================================================================

/// Encode a 32-bit float to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_float32(value: f32) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a 64-bit float to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_float64(value: f64) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a 16-bit signed integer to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_int16(value: i16) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a 32-bit signed integer to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_int32(value: i32) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a 16-bit unsigned integer to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_uint16(value: u16) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a 32-bit unsigned integer to big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_uint32(value: u32) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

/// Encode a boolean as 4-byte big-endian uint32 (Nanonis uses 4-byte bools)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_bool(value: bool) -> Vec<u8> {
    let int_val: u32 = if value { 1 } else { 0 };
    int_val.to_be_bytes().to_vec()
}

// ============================================================================
// DECODERS
// ============================================================================

/// Decode a 32-bit float from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_float32(data: Vec<u8>) -> PyResult<f32> {
    let bytes: [u8; 4] = data
        .get(..4)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for float32".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for float32".to_string()))?;
    Ok(f32::from_be_bytes(bytes))
}

/// Decode a 64-bit float from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_float64(data: Vec<u8>) -> PyResult<f64> {
    let bytes: [u8; 8] = data
        .get(..8)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for float64".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for float64".to_string()))?;
    Ok(f64::from_be_bytes(bytes))
}

/// Decode a 16-bit signed integer from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_int16(data: Vec<u8>) -> PyResult<i16> {
    let bytes: [u8; 2] = data
        .get(..2)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for int16".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for int16".to_string()))?;
    Ok(i16::from_be_bytes(bytes))
}

/// Decode a 32-bit signed integer from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_int32(data: Vec<u8>) -> PyResult<i32> {
    let bytes: [u8; 4] = data
        .get(..4)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for int32".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for int32".to_string()))?;
    Ok(i32::from_be_bytes(bytes))
}

/// Decode a 16-bit unsigned integer from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_uint16(data: Vec<u8>) -> PyResult<u16> {
    let bytes: [u8; 2] = data
        .get(..2)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for uint16".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for uint16".to_string()))?;
    Ok(u16::from_be_bytes(bytes))
}

/// Decode a 32-bit unsigned integer from big-endian bytes
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_uint32(data: Vec<u8>) -> PyResult<u32> {
    let bytes: [u8; 4] = data
        .get(..4)
        .ok_or_else(|| NanonisError::Decoding("Not enough bytes for uint32".to_string()))?
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid bytes for uint32".to_string()))?;
    Ok(u32::from_be_bytes(bytes))
}

/// Decode a boolean from 4-byte big-endian uint32
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_bool(data: Vec<u8>) -> PyResult<bool> {
    let value = decode_uint32(data)?;
    Ok(value != 0)
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_float32_roundtrip() {
        let values = [0.0f32, 1.0, -1.0, 3.14159, f32::MAX, f32::MIN];
        for v in values {
            let encoded = encode_float32(v);
            let decoded = decode_float32(encoded).unwrap();
            assert_eq!(v, decoded);
        }
    }

    #[test]
    fn test_float32_known_value() {
        // 1.5 in big-endian IEEE 754: 0x3FC00000
        let encoded = encode_float32(1.5);
        assert_eq!(encoded, vec![0x3f, 0xc0, 0x00, 0x00]);
    }

    #[test]
    fn test_int32_roundtrip() {
        let values = [0i32, 1, -1, 42, -42, i32::MAX, i32::MIN];
        for v in values {
            let encoded = encode_int32(v);
            let decoded = decode_int32(encoded).unwrap();
            assert_eq!(v, decoded);
        }
    }

    #[test]
    fn test_int32_known_value() {
        // -42 in big-endian: 0xFFFFFFD6
        let encoded = encode_int32(-42);
        assert_eq!(encoded, vec![0xff, 0xff, 0xff, 0xd6]);
    }

    #[test]
    fn test_bool() {
        assert_eq!(encode_bool(true), vec![0, 0, 0, 1]);
        assert_eq!(encode_bool(false), vec![0, 0, 0, 0]);
        assert!(decode_bool(vec![0, 0, 0, 1]).unwrap());
        assert!(!decode_bool(vec![0, 0, 0, 0]).unwrap());
    }
}
