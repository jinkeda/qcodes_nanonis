//! Array and matrix encoders/decoders
//!
//! Arrays: 4-byte size + elements
//! Matrices: 4-byte rows + 4-byte cols + elements (row-major)

use crate::errors::NanonisError;
use numpy::{PyArray1, PyArray2, PyArrayMethods};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use super::strings::{decode_string_impl, encode_string};

// ============================================================================
// ARRAY ENCODERS
// ============================================================================

/// Encode a 1D float32 array
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_array_float32(data: Vec<f32>) -> Vec<u8> {
    let mut result = Vec::with_capacity(4 + data.len() * 4);
    result.extend_from_slice(&(data.len() as u32).to_be_bytes());
    for v in data {
        result.extend_from_slice(&v.to_be_bytes());
    }
    result
}

/// Encode a 1D float64 array
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_array_float64(data: Vec<f64>) -> Vec<u8> {
    let mut result = Vec::with_capacity(4 + data.len() * 8);
    result.extend_from_slice(&(data.len() as u32).to_be_bytes());
    for v in data {
        result.extend_from_slice(&v.to_be_bytes());
    }
    result
}

/// Encode a 1D int32 array
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_array_int32(data: Vec<i32>) -> Vec<u8> {
    let mut result = Vec::with_capacity(4 + data.len() * 4);
    result.extend_from_slice(&(data.len() as u32).to_be_bytes());
    for v in data {
        result.extend_from_slice(&v.to_be_bytes());
    }
    result
}

/// Encode a 1D string array
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_array_string(data: Vec<String>) -> Vec<u8> {
    let mut result = Vec::new();
    result.extend_from_slice(&(data.len() as u32).to_be_bytes());
    for s in data {
        result.extend(encode_string(&s));
    }
    result
}

// ============================================================================
// ARRAY DECODERS
// ============================================================================

/// Decode a 1D float32 array from raw bytes.
/// Allocates the NumPy array directly to avoid an intermediate Vec copy.
pub(crate) fn decode_array_float32_from_bytes<'py>(
    py: Python<'py>,
    data: &[u8],
    count: Option<usize>,
) -> PyResult<(Bound<'py, PyArray1<f32>>, usize)> {
    let (size, offset) = if let Some(count) = count {
        (count, 0usize)
    } else {
        if data.len() < 4 {
            return Err(
                NanonisError::Decoding("Not enough bytes for array size".to_string()).into(),
            );
        }
        (u32::from_be_bytes(data[..4].try_into().unwrap()) as usize, 4usize)
    };

    let byte_len = size
        .checked_mul(4)
        .ok_or_else(|| NanonisError::Decoding("float32 array size overflow".to_string()))?;
    let expected_len = offset
        .checked_add(byte_len)
        .ok_or_else(|| NanonisError::Decoding("float32 array size overflow".to_string()))?;

    if data.len() < expected_len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for float32 array: need {} but have {}",
            expected_len,
            data.len()
        ))
        .into());
    }

    let arr = PyArray1::<f32>::zeros(py, size, false);
    let slice = unsafe { arr.as_slice_mut() }
        .map_err(|e| NanonisError::Decoding(e.to_string()))?;
    for (chunk, slot) in data[offset..expected_len]
        .chunks_exact(4)
        .zip(slice.iter_mut())
    {
        let bytes: [u8; 4] = chunk.try_into().unwrap();
        *slot = f32::from_be_bytes(bytes);
    }

    Ok((arr, expected_len))
}

/// Decode a 1D float64 array from raw bytes.
pub(crate) fn decode_array_float64_from_bytes<'py>(
    py: Python<'py>,
    data: &[u8],
    count: Option<usize>,
) -> PyResult<(Bound<'py, PyArray1<f64>>, usize)> {
    let (size, offset) = if let Some(count) = count {
        (count, 0usize)
    } else {
        if data.len() < 4 {
            return Err(
                NanonisError::Decoding("Not enough bytes for array size".to_string()).into(),
            );
        }
        (u32::from_be_bytes(data[..4].try_into().unwrap()) as usize, 4usize)
    };

    let byte_len = size
        .checked_mul(8)
        .ok_or_else(|| NanonisError::Decoding("float64 array size overflow".to_string()))?;
    let expected_len = offset
        .checked_add(byte_len)
        .ok_or_else(|| NanonisError::Decoding("float64 array size overflow".to_string()))?;

    if data.len() < expected_len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for float64 array: need {} but have {}",
            expected_len,
            data.len()
        ))
        .into());
    }

    let arr = PyArray1::<f64>::zeros(py, size, false);
    let slice = unsafe { arr.as_slice_mut() }
        .map_err(|e| NanonisError::Decoding(e.to_string()))?;
    for (chunk, slot) in data[offset..expected_len]
        .chunks_exact(8)
        .zip(slice.iter_mut())
    {
        let bytes: [u8; 8] = chunk.try_into().unwrap();
        *slot = f64::from_be_bytes(bytes);
    }

    Ok((arr, expected_len))
}

/// Decode a 1D int32 array from raw bytes.
pub(crate) fn decode_array_int32_from_bytes<'py>(
    py: Python<'py>,
    data: &[u8],
    count: Option<usize>,
) -> PyResult<(Bound<'py, PyArray1<i32>>, usize)> {
    let (size, offset) = if let Some(count) = count {
        (count, 0usize)
    } else {
        if data.len() < 4 {
            return Err(
                NanonisError::Decoding("Not enough bytes for array size".to_string()).into(),
            );
        }
        (u32::from_be_bytes(data[..4].try_into().unwrap()) as usize, 4usize)
    };

    let byte_len = size
        .checked_mul(4)
        .ok_or_else(|| NanonisError::Decoding("int32 array size overflow".to_string()))?;
    let expected_len = offset
        .checked_add(byte_len)
        .ok_or_else(|| NanonisError::Decoding("int32 array size overflow".to_string()))?;

    if data.len() < expected_len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for int32 array: need {} but have {}",
            expected_len,
            data.len()
        ))
        .into());
    }

    let arr = PyArray1::<i32>::zeros(py, size, false);
    let slice = unsafe { arr.as_slice_mut() }
        .map_err(|e| NanonisError::Decoding(e.to_string()))?;
    for (chunk, slot) in data[offset..expected_len]
        .chunks_exact(4)
        .zip(slice.iter_mut())
    {
        let bytes: [u8; 4] = chunk.try_into().unwrap();
        *slot = i32::from_be_bytes(bytes);
    }

    Ok((arr, expected_len))
}

/// Decode a 1D string array from raw bytes.
pub(crate) fn decode_array_string_from_bytes(
    data: &[u8],
    count: Option<usize>,
) -> PyResult<(Vec<String>, usize)> {
    let (size, mut offset) = if let Some(count) = count {
        (count, 0usize)
    } else {
        if data.len() < 4 {
            return Err(
                NanonisError::Decoding("Not enough bytes for array size".to_string()).into(),
            );
        }
        (u32::from_be_bytes(data[..4].try_into().unwrap()) as usize, 4usize)
    };

    let mut strings = Vec::with_capacity(size);
    for _ in 0..size {
        let (s, consumed) = decode_string_impl(&data[offset..])?;
        strings.push(s);
        offset += consumed;
    }

    Ok((strings, offset))
}

/// Decode a 2D float32 matrix from raw bytes (row-major).
pub(crate) fn decode_matrix_float32_from_bytes<'py>(
    py: Python<'py>,
    data: &[u8],
    dims: Option<(usize, usize)>,
) -> PyResult<(Bound<'py, PyArray2<f32>>, usize)> {
    let (rows, cols, offset) = if let Some((rows, cols)) = dims {
        (rows, cols, 0usize)
    } else {
        if data.len() < 8 {
            return Err(NanonisError::Decoding(
                "Not enough bytes for matrix dimensions".to_string(),
            )
            .into());
        }
        let rows = u32::from_be_bytes(data[..4].try_into().unwrap()) as usize;
        let cols = u32::from_be_bytes(data[4..8].try_into().unwrap()) as usize;
        (rows, cols, 8usize)
    };

    let elements = rows
        .checked_mul(cols)
        .ok_or_else(|| NanonisError::Decoding("matrix size overflow".to_string()))?;
    let byte_len = elements
        .checked_mul(4)
        .ok_or_else(|| NanonisError::Decoding("matrix byte size overflow".to_string()))?;
    let expected_len = offset
        .checked_add(byte_len)
        .ok_or_else(|| NanonisError::Decoding("matrix byte size overflow".to_string()))?;

    if data.len() < expected_len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for {}x{} matrix: need {} but have {}",
            rows,
            cols,
            expected_len,
            data.len()
        ))
        .into());
    }

    let arr = PyArray2::<f32>::zeros(py, [rows, cols], false);
    let slice = unsafe { arr.as_slice_mut() }
        .map_err(|e| NanonisError::Decoding(e.to_string()))?;
    for (chunk, slot) in data[offset..expected_len]
        .chunks_exact(4)
        .zip(slice.iter_mut())
    {
        let bytes: [u8; 4] = chunk.try_into().unwrap();
        *slot = f32::from_be_bytes(bytes);
    }

    Ok((arr, expected_len))
}

/// Decode a 1D float32 array to NumPy
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_float32<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_float32_from_bytes(py, data, None)?;
    Ok(arr)
}

/// Decode a 1D float64 array to NumPy
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_float64<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_float64_from_bytes(py, data, None)?;
    Ok(arr)
}

/// Decode a 1D int32 array to NumPy
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_int32<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
) -> PyResult<Bound<'py, PyArray1<i32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_int32_from_bytes(py, data, None)?;
    Ok(arr)
}

/// Decode a 1D string array
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_string<'py>(data: Bound<'py, PyBytes>) -> PyResult<Vec<String>> {
    let data = data.as_bytes();
    let (strings, _) = decode_array_string_from_bytes(data, None)?;
    Ok(strings)
}

// ============================================================================
// EXTERNAL COUNT/DIMS DECODERS (Nanonis standard format)
// ============================================================================
// Nanonis protocol provides array counts and matrix dimensions as separate
// fields rather than embedding them in the data. These functions accept
// the count/dims as parameters.

/// Decode a 1D float32 array with external count (no count prefix in data)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_float32_ext<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
    count: u32,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_float32_from_bytes(py, data, Some(count as usize))?;
    Ok(arr)
}

/// Decode a 1D float64 array with external count (no count prefix in data)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_float64_ext<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
    count: u32,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_float64_from_bytes(py, data, Some(count as usize))?;
    Ok(arr)
}

/// Decode a 1D int32 array with external count (no count prefix in data)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_int32_ext<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
    count: u32,
) -> PyResult<Bound<'py, PyArray1<i32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_array_int32_from_bytes(py, data, Some(count as usize))?;
    Ok(arr)
}

/// Decode a 1D string array with external count (no count prefix in data)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_array_string_ext<'py>(data: Bound<'py, PyBytes>, count: u32) -> PyResult<Vec<String>> {
    let data = data.as_bytes();
    let (strings, _) = decode_array_string_from_bytes(data, Some(count as usize))?;
    Ok(strings)
}

/// Decode a 2D float32 matrix with external dimensions (no dims prefix in data)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_matrix_float32_ext<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
    rows: u32,
    cols: u32,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_matrix_float32_from_bytes(py, data, Some((rows as usize, cols as usize)))?;
    Ok(arr)
}

// ============================================================================
// MATRIX ENCODERS/DECODERS
// ============================================================================

/// Encode a 2D float32 matrix (row-major)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn encode_matrix_float32(data: Vec<Vec<f32>>) -> PyResult<Vec<u8>> {
    let rows = data.len() as u32;
    let cols = if rows > 0 { data[0].len() as u32 } else { 0 };

    let mut result = Vec::with_capacity(8 + (rows as usize) * (cols as usize) * 4);
    result.extend_from_slice(&rows.to_be_bytes());
    result.extend_from_slice(&cols.to_be_bytes());

    for (i, row) in data.iter().enumerate() {
        if row.len() as u32 != cols {
            return Err(NanonisError::Encoding(format!(
                "Matrix must be rectangular. Row {} has length {}, expected {}",
                i,
                row.len(),
                cols
            ))
            .into());
        }
        for v in row {
            result.extend_from_slice(&v.to_be_bytes());
        }
    }
    Ok(result)
}

/// Decode a 2D float32 matrix to NumPy
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_matrix_float32<'py>(
    py: Python<'py>,
    data: Bound<'py, PyBytes>,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let data = data.as_bytes();
    let (arr, _) = decode_matrix_float32_from_bytes(py, data, None)?;
    Ok(arr)
}

#[cfg(test)]
/// Generic helper to decode a numeric array for tests.
fn decode_numeric_array_generic<T, F>(
    data: &[u8],
    element_size: usize,
    type_name: &str,
    decode_fn: F,
) -> PyResult<Vec<T>>
where
    F: Fn(&[u8]) -> T,
{
    if data.len() < 4 {
        return Err(NanonisError::Decoding("Not enough bytes for array size".to_string()).into());
    }

    let size = u32::from_be_bytes(data[..4].try_into().unwrap()) as usize;
    let expected_len = 4 + size * element_size;

    if data.len() < expected_len {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for {} array: need {} but have {}",
            type_name,
            expected_len,
            data.len()
        ))
        .into());
    }

    let mut values = Vec::with_capacity(size);
    for i in 0..size {
        let offset = 4 + i * element_size;
        values.push(decode_fn(&data[offset..offset + element_size]));
    }

    Ok(values)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn test_array_float32_encode() {
        let arr = vec![1.0f32, 2.0, 3.0];
        let encoded = encode_array_float32(arr);
        // Size = 3, then three float32s
        assert_eq!(&encoded[..4], &[0, 0, 0, 3]);
        assert_eq!(encoded.len(), 4 + 3 * 4);
    }

    #[test]
    fn test_array_string_encode() {
        let arr = vec!["hello".to_string(), "world".to_string()];
        let encoded = encode_array_string(arr);
        // Size = 2, then two length-prefixed strings
        assert_eq!(&encoded[..4], &[0, 0, 0, 2]);
    }

    #[test]
    fn test_matrix_float32_encode() {
        let mat = vec![vec![1.0f32, 2.0], vec![3.0, 4.0]];
        let encoded = encode_matrix_float32(mat).unwrap();
        // Rows = 2, cols = 2
        assert_eq!(&encoded[..4], &[0, 0, 0, 2]);
        assert_eq!(&encoded[4..8], &[0, 0, 0, 2]);
        assert_eq!(encoded.len(), 8 + 4 * 4);
    }

    #[test]
    fn test_array_float32_decode() {
        // Size = 2, val = [1.0, 2.0]
        let data = vec![
            0, 0, 0, 2, // Size
            0x3f, 0x80, 0x00, 0x00, // 1.0
            0x40, 0x00, 0x00, 0x00, // 2.0
        ];

        // Access internal decode function implicitly?
        // decode_numeric_array_generic is not pub.
        // But we are in "super", so we can access it.
        let values: Vec<f32> = super::decode_numeric_array_generic(&data, 4, "float32", |b| {
            f32::from_be_bytes(b.try_into().unwrap())
        })
        .unwrap();

        assert_eq!(values, vec![1.0, 2.0]);
    }

    #[test]
    fn test_array_string_empty() {
        let encoded = encode_array_string(Vec::new());
        assert_eq!(&encoded[..4], &[0, 0, 0, 0]);
    }

    #[test]
    fn test_array_float32_large() {
        let values: Vec<f32> = (0..4096).map(|v| v as f32).collect();
        let encoded = encode_array_float32(values.clone());
        let decoded: Vec<f32> = super::decode_numeric_array_generic(
            &encoded,
            4,
            "float32",
            |b| f32::from_be_bytes(b.try_into().unwrap()),
        )
        .unwrap();
        assert_eq!(decoded.len(), values.len());
        for (a, b) in decoded.iter().zip(values.iter()) {
            assert_eq!(a.to_bits(), b.to_bits());
        }
    }

    #[test]
    fn test_array_int32_single() {
        let values = vec![42i32];
        let encoded = encode_array_int32(values.clone());
        let decoded: Vec<i32> = super::decode_numeric_array_generic(
            &encoded,
            4,
            "int32",
            |b| i32::from_be_bytes(b.try_into().unwrap()),
        )
        .unwrap();
        assert_eq!(decoded, values);
    }

    proptest! {
        #[test]
        fn proptest_array_float32_roundtrip(values in proptest::collection::vec(any::<f32>(), 0..256)) {
            let encoded = encode_array_float32(values.clone());
            let decoded: Vec<f32> = super::decode_numeric_array_generic(
                &encoded,
                4,
                "float32",
                |b| f32::from_be_bytes(b.try_into().unwrap()),
            )
            .unwrap();
            prop_assert_eq!(decoded.len(), values.len());
            for (a, b) in decoded.iter().zip(values.iter()) {
                prop_assert_eq!(a.to_bits(), b.to_bits());
            }
        }

        #[test]
        fn proptest_array_float64_roundtrip(values in proptest::collection::vec(any::<f64>(), 0..128)) {
            let encoded = encode_array_float64(values.clone());
            let decoded: Vec<f64> = super::decode_numeric_array_generic(
                &encoded,
                8,
                "float64",
                |b| f64::from_be_bytes(b.try_into().unwrap()),
            )
            .unwrap();
            prop_assert_eq!(decoded.len(), values.len());
            for (a, b) in decoded.iter().zip(values.iter()) {
                prop_assert_eq!(a.to_bits(), b.to_bits());
            }
        }

        #[test]
        fn proptest_array_int32_roundtrip(values in proptest::collection::vec(any::<i32>(), 0..256)) {
            let encoded = encode_array_int32(values.clone());
            let decoded: Vec<i32> = super::decode_numeric_array_generic(
                &encoded,
                4,
                "int32",
                |b| i32::from_be_bytes(b.try_into().unwrap()),
            )
            .unwrap();
            prop_assert_eq!(decoded, values);
        }
    }
}
