//! Error types for Nanonis protocol

use pyo3::exceptions::{PyConnectionError, PyTimeoutError, PyValueError};
use pyo3::prelude::*;
use thiserror::Error;

/// Nanonis protocol error types
#[derive(Error, Debug)]
pub enum NanonisError {
    #[error("Connection failed: {0}")]
    Connection(String),

    #[error("Timeout after {0} seconds")]
    Timeout(f64),

    #[error("Protocol error: {0}")]
    Protocol(String),

    #[error("Command error: {0}")]
    Command(String),

    #[error("Encoding error: {0}")]
    Encoding(String),

    #[error("Decoding error: {0}")]
    Decoding(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

impl From<NanonisError> for PyErr {
    fn from(err: NanonisError) -> PyErr {
        match err {
            NanonisError::Connection(msg) => PyConnectionError::new_err(msg),
            NanonisError::Timeout(secs) => {
                PyTimeoutError::new_err(format!("Timeout after {} seconds", secs))
            }
            NanonisError::Protocol(msg) => PyValueError::new_err(format!("Protocol: {}", msg)),
            NanonisError::Command(msg) => PyValueError::new_err(format!("Command: {}", msg)),
            NanonisError::Encoding(msg) => PyValueError::new_err(format!("Encoding: {}", msg)),
            NanonisError::Decoding(msg) => PyValueError::new_err(format!("Decoding: {}", msg)),
            NanonisError::Io(e) => PyConnectionError::new_err(e.to_string()),
        }
    }
}

/// Shorthand Result type for Nanonis operations
pub type Result<T> = std::result::Result<T, NanonisError>;
