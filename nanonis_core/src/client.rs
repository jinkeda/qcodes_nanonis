//! TCP client for Nanonis communication

use crate::errors::{NanonisError, Result};
use crate::header::{decode_header, encode_header, HEADER_SIZE};

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::io::{BufReader, BufWriter, Read, Write};
use std::net::TcpStream;
use std::time::Duration;

/// Nanonis TCP client with buffered I/O
#[pyclass]
pub struct NanonisTcpClient {
    reader: Option<BufReader<TcpStream>>,
    writer: Option<BufWriter<TcpStream>>,
    host: String,
    port: u16,
    timeout_secs: f64,
}

#[pymethods]
impl NanonisTcpClient {
    /// Create a new TCP client
    ///
    /// # Arguments
    /// * `host` - Nanonis host IP address
    /// * `port` - Nanonis TCP port (typically 6501)
    /// * `timeout` - Socket timeout in seconds
    #[new]
    pub fn new(host: String, port: u16, timeout: f64) -> Self {
        NanonisTcpClient {
            reader: None,
            writer: None,
            host,
            port,
            timeout_secs: timeout,
        }
    }

    /// Check if connected
    #[getter]
    pub fn is_connected(&self) -> bool {
        self.reader.is_some() && self.writer.is_some()
    }

    /// Establish TCP connection to Nanonis
    pub fn connect(&mut self) -> PyResult<()> {
        // Disconnect if already connected
        if self.is_connected() {
            self.disconnect()?;
        }

        let addr = format!("{}:{}", self.host, self.port);
        let timeout = Duration::from_secs_f64(self.timeout_secs);

        let stream = TcpStream::connect_timeout(
            &addr.parse().map_err(|e| {
                NanonisError::Connection(format!("Invalid address {}: {}", addr, e))
            })?,
            timeout,
        )
        .map_err(|e| NanonisError::Connection(format!("Failed to connect to {}: {}", addr, e)))?;

        stream
            .set_read_timeout(Some(timeout))
            .map_err(|e| NanonisError::Connection(format!("Failed to set read timeout: {}", e)))?;
        stream
            .set_write_timeout(Some(timeout))
            .map_err(|e| NanonisError::Connection(format!("Failed to set write timeout: {}", e)))?;

        // Clone stream for reader (TcpStream can be cloned)
        let read_stream = stream
            .try_clone()
            .map_err(|e| NanonisError::Connection(format!("Failed to clone stream: {}", e)))?;

        self.reader = Some(BufReader::new(read_stream));
        self.writer = Some(BufWriter::new(stream));

        Ok(())
    }

    /// Close the TCP connection
    pub fn disconnect(&mut self) -> PyResult<()> {
        self.reader = None;
        self.writer = None;
        Ok(())
    }

    /// Send a raw command to Nanonis and receive the response
    ///
    /// # Arguments
    /// * `command` - Command name (e.g., 'Bias.Get')
    /// * `body` - Encoded command body bytes
    ///
    /// # Returns
    /// Response body bytes (as PyBytes to avoid copy)
    pub fn send_raw<'py>(
        &mut self,
        py: Python<'py>,
        command: &str,
        body: &[u8],
    ) -> PyResult<Bound<'py, PyBytes>> {
        let response = self.internal_send_raw(command, body)?;
        Ok(PyBytes::new(py, &response))
    }

    /// Send with custom timeout (for long operations)
    pub fn send_raw_with_timeout<'py>(
        &mut self,
        py: Python<'py>,
        command: &str,
        body: &[u8],
        timeout_secs: f64,
    ) -> PyResult<Bound<'py, PyBytes>> {
        // Save original timeout
        let original_timeout = self.timeout_secs;

        // Set temporary timeout
        if let Some(ref reader) = self.reader {
            let timeout = Duration::from_secs_f64(timeout_secs);
            reader
                .get_ref()
                .set_read_timeout(Some(timeout))
                .map_err(|e| NanonisError::Connection(format!("Failed to set timeout: {}", e)))?;
        }

        // Send command
        let result = self.internal_send_raw(command, body);

        // Restore original timeout
        if let Some(ref reader) = self.reader {
            let timeout = Duration::from_secs_f64(original_timeout);
            let _ = reader.get_ref().set_read_timeout(Some(timeout));
        }

        Ok(PyBytes::new(py, &result?))
    }

    fn __repr__(&self) -> String {
        let status = if self.is_connected() {
            "connected"
        } else {
            "disconnected"
        };
        format!(
            "NanonisTcpClient('{}', {}, {})",
            self.host, self.port, status
        )
    }

    fn __enter__(slf: Py<Self>) -> Py<Self> {
        slf
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        &mut self,
        _exc_type: Option<Bound<'_, pyo3::types::PyType>>,
        _exc_val: Option<Bound<'_, pyo3::types::PyAny>>,
        _exc_tb: Option<Bound<'_, pyo3::types::PyAny>>,
    ) -> PyResult<bool> {
        self.disconnect()?;
        Ok(false) // Don't suppress exceptions
    }
}

impl NanonisTcpClient {
    /// Internal send/receive implementation
    fn internal_send_raw(&mut self, command: &str, body: &[u8]) -> Result<Vec<u8>> {
        let writer = self
            .writer
            .as_mut()
            .ok_or_else(|| NanonisError::Connection("Not connected to Nanonis".into()))?;
        let reader = self
            .reader
            .as_mut()
            .ok_or_else(|| NanonisError::Connection("Not connected to Nanonis".into()))?;

        // Encode and send header + body
        let header = encode_header(command, body.len());
        writer.write_all(&header)?;
        if !body.is_empty() {
            writer.write_all(body)?;
        }
        writer.flush()?;

        // Receive response header
        let mut response_header = [0u8; HEADER_SIZE];
        reader.read_exact(&mut response_header)?;

        // Decode header to get body size
        let (_, body_size, _) = decode_header(&response_header)?;

        // Receive response body
        let mut response_body = vec![0u8; body_size];
        if body_size > 0 {
            reader.read_exact(&mut response_body)?;
        }

        Ok(response_body)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = NanonisTcpClient::new("127.0.0.1".into(), 6501, 10.0);
        assert!(!client.is_connected());
        assert_eq!(client.host, "127.0.0.1");
        assert_eq!(client.port, 6501);
    }
}

