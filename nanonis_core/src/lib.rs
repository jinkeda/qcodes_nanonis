//! Nanonis Core - Rust TCP protocol and binary encoding library
//!
//! # Python API
//!
//! This module exports the core functionality for the Nanonis TCP protocol to Python.
//! It includes:
//!
//! ## NanonisTcpClient
//! The main client class for communicating with the Nanonis controller.
//!
//! ## Codec Functions
//! Binary encoding and decoding functions for Nanonis protocol data types.
//!
//! ### Scalar Types
//! - `encode_float32/64`, `encode_int16/32/u16/u32`
//! - `decode_float32/64`, `decode_int16/32/u16/u32`
//! - `encode_bool`, `decode_bool`
//! - `encode_string`, `decode_string`, `decode_string_simple`
//!
//! ### Array Types
//! - `encode_array_float32/64`, `encode_array_int32`, `encode_array_string`
//! - `decode_array_float32/64`, `decode_array_int32`, `decode_array_string`
//!
//! ### Matrix Types
//! - `encode_matrix_float32`: Encodes a 2D numpy array (must be rectangular).
//! - `decode_matrix_float32`: Decodes a 2D float32 matrix.
//!

use pyo3::prelude::*;
use pyo3_stub_gen::define_stub_info_gatherer;

mod client;
mod codec;
mod errors;
mod header;

pub use client::NanonisTcpClient;
pub use errors::NanonisError;

// Define stub_info gatherer function for Python stub generation
define_stub_info_gatherer!(stub_info);

/// Python module initialization
#[pymodule]
fn nanonis_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // TCP Client
    m.add_class::<NanonisTcpClient>()?;

    // Scalar encoders
    m.add_function(wrap_pyfunction!(codec::encode_float32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_float64, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_int16, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_int32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_uint16, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_uint32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_bool, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_string, m)?)?;

    // Scalar decoders
    m.add_function(wrap_pyfunction!(codec::decode_float32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_float64, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_int16, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_int32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_uint16, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_uint32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_bool, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_string, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_string_simple, m)?)?;

    // Array encoders
    m.add_function(wrap_pyfunction!(codec::encode_array_float32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_array_float64, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_array_int32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::encode_array_string, m)?)?;

    // Array decoders
    m.add_function(wrap_pyfunction!(codec::decode_array_float32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_array_float64, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_array_int32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_array_string, m)?)?;

    // Matrix encoders/decoders
    m.add_function(wrap_pyfunction!(codec::encode_matrix_float32, m)?)?;
    m.add_function(wrap_pyfunction!(codec::decode_matrix_float32, m)?)?;

    Ok(())
}
