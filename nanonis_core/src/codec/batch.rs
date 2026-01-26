//! Batch decoding helpers to reduce FFI overhead.
//!
//! Decodes a list of (name, dtype) tuples in a single call.

use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use crate::errors::NanonisError;

use super::arrays::{
    decode_array_float32_from_bytes, decode_array_float64_from_bytes, decode_array_int32_from_bytes,
    decode_array_string_from_bytes, decode_matrix_float32_from_bytes,
};
use super::strings::decode_string_impl;

fn is_int_dtype(dtype: &str) -> bool {
    matches!(dtype, "int16" | "int32" | "uint16" | "uint32")
}

fn get_external_count(
    array_name: &str,
    prefixes: &HashMap<String, String>,
    values: &HashMap<String, i64>,
) -> Option<usize> {
    for (prefix, field_name) in prefixes {
        if array_name == prefix
            || array_name.starts_with(prefix)
            || array_name.starts_with(&format!("{prefix}_"))
        {
            if let Some(value) = values.get(field_name) {
                if *value >= 0 {
                    return Some(*value as usize);
                }
            }
        }
    }
    None
}

fn get_external_dims(
    matrix_name: &str,
    dims: &HashMap<String, (Option<String>, Option<String>)>,
    values: &HashMap<String, i64>,
) -> Option<(usize, usize)> {
    if let Some((rows_field, cols_field)) = dims.get(matrix_name) {
        if let (Some(rows_field), Some(cols_field)) = (rows_field, cols_field) {
            if let (Some(rows), Some(cols)) = (values.get(rows_field), values.get(cols_field)) {
                if *rows >= 0 && *cols >= 0 {
                    return Some((*rows as usize, *cols as usize));
                }
            }
        }
    }
    None
}

fn require_bytes<'a>(data: &'a [u8], offset: usize, size: usize, type_name: &str) -> PyResult<&'a [u8]> {
    let end = offset
        .checked_add(size)
        .ok_or_else(|| NanonisError::Decoding(format!("{type_name} offset overflow")))?;
    if data.len() < end {
        return Err(NanonisError::Decoding(format!(
            "Not enough bytes for {}: need {} but have {}",
            type_name,
            end,
            data.len()
        ))
        .into());
    }
    Ok(&data[offset..end])
}

/// Decode a full message in one Rust call.
///
/// Args:
///     schema: List of (name, dtype) tuples
///     data: Raw response bytes
///
/// Returns:
///     (values, bytes_consumed)
#[gen_stub_pyfunction]
#[pyfunction]
pub fn decode_message<'py>(
    py: Python<'py>,
    schema: Vec<(String, String)>,
    data: Bound<'py, PyBytes>,
) -> PyResult<(Vec<PyObject>, usize)> {
    let data = data.as_bytes();
    let mut offset = 0usize;
    let mut results = Vec::with_capacity(schema.len());

    // Track previously-decoded integer fields for external counts/dims.
    let mut int_values: HashMap<String, i64> = HashMap::new();

    // Pre-scan schema for external count/dims fields.
    let mut external_count_prefixes: HashMap<String, String> = HashMap::new();
    let mut external_matrix_dims: HashMap<String, (Option<String>, Option<String>)> = HashMap::new();

    for (name, dtype) in &schema {
        if is_int_dtype(dtype) {
            if let Some(prefix) = name.strip_prefix("num_") {
                external_count_prefixes.insert(prefix.to_string(), name.clone());
            } else if let Some(prefix) = name.strip_suffix("_count") {
                external_count_prefixes.insert(prefix.to_string(), name.clone());
            } else if let Some(base) = name.strip_suffix("_rows") {
                external_matrix_dims
                    .entry(base.to_string())
                    .or_insert_with(|| (None, None))
                    .0 = Some(name.clone());
            } else if let Some(base) = name.strip_suffix("_columns") {
                external_matrix_dims
                    .entry(base.to_string())
                    .or_insert_with(|| (None, None))
                    .1 = Some(name.clone());
            }
        }
    }

    for (name, dtype) in schema {
        match dtype.as_str() {
            "float32" => {
                let bytes = require_bytes(data, offset, 4, "float32")?;
                let value = f32::from_be_bytes(bytes.try_into().unwrap());
                offset += 4;
                results.push(value.into_py(py));
            }
            "float64" => {
                let bytes = require_bytes(data, offset, 8, "float64")?;
                let value = f64::from_be_bytes(bytes.try_into().unwrap());
                offset += 8;
                results.push(value.into_py(py));
            }
            "int16" => {
                let bytes = require_bytes(data, offset, 2, "int16")?;
                let value = i16::from_be_bytes(bytes.try_into().unwrap());
                offset += 2;
                results.push(value.into_py(py));
                int_values.insert(name, value as i64);
            }
            "int32" => {
                let bytes = require_bytes(data, offset, 4, "int32")?;
                let value = i32::from_be_bytes(bytes.try_into().unwrap());
                offset += 4;
                results.push(value.into_py(py));
                int_values.insert(name, value as i64);
            }
            "uint16" => {
                let bytes = require_bytes(data, offset, 2, "uint16")?;
                let value = u16::from_be_bytes(bytes.try_into().unwrap());
                offset += 2;
                results.push(value.into_py(py));
                int_values.insert(name, value as i64);
            }
            "uint32" => {
                let bytes = require_bytes(data, offset, 4, "uint32")?;
                let value = u32::from_be_bytes(bytes.try_into().unwrap());
                offset += 4;
                results.push(value.into_py(py));
                int_values.insert(name, value as i64);
            }
            "bool" => {
                let bytes = require_bytes(data, offset, 4, "bool")?;
                let value = u32::from_be_bytes(bytes.try_into().unwrap()) != 0;
                offset += 4;
                results.push(value.into_py(py));
            }
            "string" => {
                let (value, consumed) = decode_string_impl(&data[offset..])?;
                offset += consumed;
                results.push(value.into_py(py));
            }
            "array_float32" => {
                let count = get_external_count(&name, &external_count_prefixes, &int_values);
                let (arr, consumed) = decode_array_float32_from_bytes(py, &data[offset..], count)?;
                offset += consumed;
                results.push(arr.into_py(py));
            }
            "array_float64" => {
                let count = get_external_count(&name, &external_count_prefixes, &int_values);
                let (arr, consumed) = decode_array_float64_from_bytes(py, &data[offset..], count)?;
                offset += consumed;
                results.push(arr.into_py(py));
            }
            "array_int32" => {
                let count = get_external_count(&name, &external_count_prefixes, &int_values);
                let (arr, consumed) = decode_array_int32_from_bytes(py, &data[offset..], count)?;
                offset += consumed;
                results.push(arr.into_py(py));
            }
            "array_string" => {
                let count = get_external_count(&name, &external_count_prefixes, &int_values);
                let (strings, consumed) = decode_array_string_from_bytes(&data[offset..], count)?;
                offset += consumed;
                results.push(strings.into_py(py));
            }
            "matrix_float32" => {
                let dims = get_external_dims(&name, &external_matrix_dims, &int_values);
                let (arr, consumed) = decode_matrix_float32_from_bytes(py, &data[offset..], dims)?;
                offset += consumed;
                results.push(arr.into_py(py));
            }
            other => {
                return Err(NanonisError::Decoding(format!(
                    "Unsupported dtype in batch decode: {}",
                    other
                ))
                .into());
            }
        }
    }

    Ok((results, offset))
}
