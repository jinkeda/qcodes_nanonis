# -*- coding: utf-8 -*-
"""
Nanonis TCP Client

Low-level TCP communication with the Nanonis controller.
Handles connection, header encoding/decoding, and raw byte transmission.
"""

import socket
import struct
from typing import Optional

from .exceptions import (
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)


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
    
    @property
    def is_connected(self) -> bool:
        """Check if socket is connected."""
        return self._socket is not None
    
    def connect(self) -> None:
        """
        Establish TCP connection to Nanonis.
        
        Raises:
            NanonisConnectionError: If connection fails
        """
        if self._socket is not None:
            self.disconnect()
        
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
        
        Args:
            command_name: Command name string
            body_size: Size of the body in bytes
            
        Returns:
            40-byte header
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
            # command_name = header[:32].rstrip(b'\x00').decode('utf-8')
            body_size = struct.unpack('>i', header[32:36])[0]
            # response_flag = struct.unpack('>H', header[36:38])[0]
            # error_flag = struct.unpack('>H', header[38:40])[0]
            
            # Receive body
            if body_size > 0:
                return self._recv_exact(body_size)
            return b''
            
        except socket.timeout as e:
            raise NanonisTimeoutError("Response timed out") from e
    
    def _recv_exact(self, size: int) -> bytes:
        """
        Receive exactly `size` bytes from the socket.
        
        Args:
            size: Number of bytes to receive
            
        Returns:
            Received bytes
            
        Raises:
            NanonisConnectionError: If connection is closed
            NanonisProtocolError: If not enough data received
        """
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
        return f"NanonisTCPClient({self.host}:{self.port}, {status})"
