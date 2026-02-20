//! String encoder and decoder
//!
//! Nanonis strings are length-prefixed: 4-byte big-endian size + UTF-8 bytes

use crate::errors::NanonisError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

/// Encode a string with length prefix (4-byte big-endian size + UTF-8)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_string(value: &str) -> Vec<u8> {
    let bytes = value.as_bytes();
    let len = bytes.len() as u32;
    let mut result = Vec::with_capacity(4 + bytes.len());
    result.extend_from_slice(&len.to_be_bytes());
    result.extend_from_slice(bytes);
    result
}

/// Decode a length-prefixed string (Implementation)
///
/// Returns (decoded_string, bytes_consumed)
pub fn decode_string_impl(data: &[u8]) -> PyResult<(String, usize)> {
    if data.len() < 4 {
        return Err(
            NanonisError::Decoding("Not enough bytes for string length".to_string()).into(),
        );
    }

    let len_bytes: [u8; 4] = data[..4]
        .try_into()
        .map_err(|_| NanonisError::Decoding("Invalid length bytes".to_string()))?;
    let len = u32::from_be_bytes(len_bytes) as usize;

    if data.len() < 4 + len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for string: need {} but have {}",
            4 + len,
            data.len()
        ))
        .into());
    }

    let string = String::from_utf8_lossy(&data[4..4 + len]).to_string();
    Ok((string, 4 + len))
}

/// Decode a length-prefixed string
///
/// Returns (decoded_string, bytes_consumed)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_string<'py>(data: Bound<'py, PyBytes>) -> PyResult<(String, usize)> {
    decode_string_impl(data.as_bytes())
}

/// Decode a string and return only the string value
///
/// This is a convenience wrapper for Python users who don't need the consumed byte count.
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_string_simple<'py>(data: Bound<'py, PyBytes>) -> PyResult<String> {
    let (s, _) = decode_string_impl(data.as_bytes())?;
    Ok(s)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Test roundtrip encoding/decoding for various string types.
    #[test]
    fn test_string_roundtrip() {
        let values = vec![
            "".to_string(),
            "hello".to_string(),
            "Bias.Get".to_string(),
            "こんにちは".to_string(),
            "a".repeat(1000),
        ];
        for v in values {
            let encoded = encode_string(&v);
            let (decoded, consumed) = decode_string_impl(&encoded).unwrap();
            assert_eq!(v, decoded);
            assert_eq!(consumed, encoded.len());
        }
    }

    #[test]
    fn test_string_known_value() {
        let encoded = encode_string("hello");
        // Length = 5 (big-endian), then "hello"
        assert_eq!(encoded, b"\x00\x00\x00\x05hello");
    }

    #[test]
    fn test_decode_string_simple() {
        // This test uses the PyFunction logic which needs GIL.
        // For simplicity, we can test decode_string_impl which is the core logic.
        // Or setup GIL.
        let encoded = encode_string("hello");
        let (s, _) = decode_string_impl(&encoded).unwrap();
        assert_eq!(s, "hello");
    }
}
