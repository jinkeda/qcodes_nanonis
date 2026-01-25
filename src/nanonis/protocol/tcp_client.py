# -*- coding: utf-8 -*-
"""
Nanonis TCP Client

Low-level TCP communication with the Nanonis controller.
Handles connection, header encoding/decoding, and raw byte transmission.
"""

import socket
import struct
import logging
from typing import Optional

from .exceptions import (
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)

logger = logging.getLogger(__name__)

# Try to import Rust backend
try:
    import nanonis_core
    RUST_BACKEND = True
    logger.info("Using optimized Rust backend for Nanonis TCP")
except ImportError:
    RUST_BACKEND = False
    logger.warning("Rust backend not found, using slower Python implementation")


class NanonisTCPClient:
    """
    Layer 1: Low-level TCP communication with Nanonis.
    
    This class handles:
    - TCP socket connection management
    - Nanonis protocol header encoding (40 bytes)
    - Sending commands and receiving responses
    
    Example:
        >>> with NanonisTCPClient('127.0.0.1', 6501) as client:
        ...     response = client.send_raw('Bias.Get', b'')
        ...     print(response)
    """
    
    HEADER_SIZE = 40
    COMMAND_NAME_SIZE = 32
    
    def __init__(self, host: str, port: int, timeout: float = 10.0):
        """
        Initialize TCP client.
        
        Args:
            host: Nanonis host IP address
            port: Nanonis TCP port (typically 6501)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._rust_client = None
        
        if RUST_BACKEND:
            try:
                self._rust_client = nanonis_core.NanonisTcpClient(host, port, timeout)
            except Exception as e:
                logger.error(f"Failed to initialize Rust client: {e}")
                self._rust_client = None
    
    @property
    def is_connected(self) -> bool:
        """Check if socket is connected."""
        if self._rust_client:
            return self._rust_client.is_connected
        return self._socket is not None
    
    def connect(self) -> None:
        """
        Establish TCP connection to Nanonis.
        
        Raises:
            NanonisConnectionError: If connection fails
        """
        if self.is_connected:
            self.disconnect()
        
        # Use Rust backend if available
        if self._rust_client:
            try:
                self._rust_client.connect()
                return
            except Exception as e:
                # Convert Rust error to Python exception
                raise NanonisConnectionError(str(e)) from e
        
        # Python fallback
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
        except socket.timeout as e:
            self._socket = None
            raise NanonisConnectionError(
                f"Connection to {self.host}:{self.port} timed out"
            ) from e
        except socket.error as e:
            self._socket = None
            raise NanonisConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {e}"
            ) from e
    
    def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._rust_client:
            try:
                self._rust_client.disconnect()
            except Exception:
                pass
                
        if self._socket is not None:
            try:
                self._socket.close()
            except socket.error:
                pass  # Ignore errors during close
            finally:
                self._socket = None
    
    def send_raw(self, command_name: str, body: bytes) -> bytes:
        """
        Send a raw command to Nanonis and receive the response.
        
        Args:
            command_name: The Nanonis command name (e.g., 'Bias.Get')
            body: The encoded command body bytes
            
        Returns:
            The response body bytes (excluding header)
            
        Raises:
            NanonisConnectionError: If not connected
            NanonisProtocolError: If response is malformed
            NanonisTimeoutError: If response times out
        """
        # Use Rust backend if available
        if self._rust_client:
            try:
                # Rust client handles header encoding/decoding internally
                # and returns bytes directly
                if not self.is_connected:
                     raise NanonisConnectionError("Not connected to Nanonis")
                return self._rust_client.send_raw(command_name, body)
            except Exception as e:
                # Map errors
                msg = str(e)
                if "Timeout" in msg:
                    raise NanonisTimeoutError(msg) from e
                elif "Protocol" in msg:
                    raise NanonisProtocolError(msg) from e
                elif "Connection" in msg or "connected" in msg:
                    raise NanonisConnectionError(msg) from e
                else:
                    raise NanonisProtocolError(f"Rust client error: {msg}") from e
        
        # Python fallback implementation
        if self._socket is None:
            raise NanonisConnectionError("Not connected to Nanonis")
        
        # Build and send request
        header = self._encode_header(command_name, len(body))
        try:
            self._socket.sendall(header + body)
        except socket.error as e:
            raise NanonisConnectionError(f"Failed to send command: {e}") from e
        
        # Receive response
        return self._receive_response()
    
    def _encode_header(self, command_name: str, body_size: int) -> bytes:
        """
        Encode the Nanonis protocol header.
        
        Header format (40 bytes total):
        - Bytes 0-31: Command name (null-padded ASCII)
        - Bytes 32-35: Body size (big-endian int32)
        - Bytes 36-37: Send flag (big-endian uint16, always 1)
        - Bytes 38-39: Reserved (big-endian uint16, always 0)
        """
        # Command name: 32 bytes, null-padded
        cmd_bytes = command_name.encode('utf-8')[:self.COMMAND_NAME_SIZE]
        cmd_bytes = cmd_bytes.ljust(self.COMMAND_NAME_SIZE, b'\x00')
        
        # Body size: 4 bytes, big-endian int32
        size_bytes = struct.pack('>i', body_size)
        
        # Flags: 4 bytes (send=1, reserved=0)
        flags = struct.pack('>HH', 1, 0)
        
        return cmd_bytes + size_bytes + flags
    
    def _receive_response(self) -> bytes:
        """
        Receive and parse the response from Nanonis.
        
        Returns:
            Response body bytes
            
        Raises:
            NanonisProtocolError: If response is malformed
            NanonisTimeoutError: If response times out
        """
        try:
            # Receive header
            header = self._recv_exact(self.HEADER_SIZE)
            
            # Parse header
            body_size = struct.unpack('>i', header[32:36])[0]
            
            # Receive body
            if body_size > 0:
                return self._recv_exact(body_size)
            return b''
            
        except socket.timeout as e:
            raise NanonisTimeoutError("Response timed out") from e
    
    def _recv_exact(self, size: int) -> bytes:
        """Receive exactly `size` bytes from the socket."""
        data = b''
        while len(data) < size:
            try:
                chunk = self._socket.recv(size - len(data))
                if not chunk:
                    raise NanonisConnectionError(
                        f"Connection closed while receiving data "
                        f"(got {len(data)}/{size} bytes)"
                    )
                data += chunk
            except socket.error as e:
                raise NanonisConnectionError(f"Receive failed: {e}") from e
        return data
    
    def __enter__(self) -> 'NanonisTCPClient':
        """Context manager entry: connect."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: disconnect."""
        self.disconnect()
    
    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        backend = "Rust" if self._rust_client else "Python"
        return f"NanonisTCPClient({self.host}:{self.port}, {status}, backend={backend})"
