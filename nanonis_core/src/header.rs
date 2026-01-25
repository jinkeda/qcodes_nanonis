//! Nanonis protocol header encoding/decoding
//!
//! Header format (40 bytes total):
//! - Bytes 0-31: Command name (null-padded ASCII)
//! - Bytes 32-35: Body size (big-endian i32)
//! - Bytes 36-37: Send flag (big-endian u16, always 1 for requests)
//! - Bytes 38-39: Reserved (big-endian u16, always 0)

use crate::errors::{NanonisError, Result};

/// Header size in bytes
pub const HEADER_SIZE: usize = 40;
/// Command name field size
pub const COMMAND_NAME_SIZE: usize = 32;

/// Encode a Nanonis protocol header
///
/// # Arguments
/// * `command` - Command name (max 32 bytes)
/// * `body_size` - Size of the body in bytes
///
/// # Returns
/// 40-byte header array
pub fn encode_header(command: &str, body_size: usize) -> [u8; HEADER_SIZE] {
    let mut header = [0u8; HEADER_SIZE];

    // Command name: 32 bytes, null-padded
    let cmd_bytes = command.as_bytes();
    let copy_len = cmd_bytes.len().min(COMMAND_NAME_SIZE);
    header[..copy_len].copy_from_slice(&cmd_bytes[..copy_len]);

    // Body size: 4 bytes, big-endian i32
    let size_bytes = (body_size as i32).to_be_bytes();
    header[32..36].copy_from_slice(&size_bytes);

    // Send flag: 2 bytes, big-endian u16 = 1
    header[36..38].copy_from_slice(&1u16.to_be_bytes());

    // Reserved: 2 bytes, big-endian u16 = 0
    // Already zero from initialization

    header
}

/// Decode a Nanonis protocol header
///
/// # Arguments
/// * `data` - 40-byte header data
///
/// # Returns
/// Tuple of (command_name, body_size, is_response)
pub fn decode_header(data: &[u8; HEADER_SIZE]) -> Result<(String, usize, bool)> {
    // Command name
    let cmd_end = data[..COMMAND_NAME_SIZE]
        .iter()
        .position(|&b| b == 0)
        .unwrap_or(COMMAND_NAME_SIZE);
    let command = String::from_utf8_lossy(&data[..cmd_end]).to_string();

    // Body size
    let size_bytes: [u8; 4] = data[32..36]
        .try_into()
        .map_err(|_| NanonisError::Protocol("Invalid header size bytes".into()))?;
    let body_size = i32::from_be_bytes(size_bytes);

    if body_size < 0 {
        return Err(NanonisError::Protocol(format!(
            "Invalid body size: {}",
            body_size
        )));
    }

    // Response flag (0 = request, 1 = response)
    let flag_bytes: [u8; 2] = data[36..38]
        .try_into()
        .map_err(|_| NanonisError::Protocol("Invalid header flag bytes".into()))?;
    let is_response = u16::from_be_bytes(flag_bytes) == 0;

    Ok((command, body_size as usize, is_response))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encode_header() {
        let header = encode_header("Bias.Get", 0);
        assert_eq!(&header[..8], b"Bias.Get");
        assert_eq!(&header[8..32], &[0u8; 24]);
        assert_eq!(&header[32..36], &[0, 0, 0, 0]); // body_size = 0
        assert_eq!(&header[36..38], &[0, 1]); // send_flag = 1
        assert_eq!(&header[38..40], &[0, 0]); // reserved = 0
    }

    #[test]
    fn test_encode_header_with_body() {
        let header = encode_header("Bias.Set", 4);
        assert_eq!(&header[32..36], &[0, 0, 0, 4]); // body_size = 4
    }

    #[test]
    fn test_roundtrip() {
        let original = encode_header("ZCtrl.OnOffGet", 128);
        let (cmd, size, _) = decode_header(&original).unwrap();
        assert_eq!(cmd, "ZCtrl.OnOffGet");
        assert_eq!(size, 128);
    }
}
