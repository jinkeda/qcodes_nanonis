# -*- coding: utf-8 -*-
"""
Tests for Protocol Layer

Tests for NanonisTCPClient and exception handling.
"""

import pytest
import socket
from unittest.mock import Mock, patch, MagicMock

from nanonis.protocol import (
    NanonisTCPClient,
    NanonisError,
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)


class _FakeRustClient:
    def __init__(self) -> None:
        self._connected = False
        self.connect = Mock(side_effect=self._connect)
        self.disconnect = Mock(side_effect=self._disconnect)

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _connect(self) -> None:
        self._connected = True

    def _disconnect(self) -> None:
        self._connected = False


def _attach_fake_rust_client(client: NanonisTCPClient) -> _FakeRustClient | None:
    if client._rust_client is None:
        return None
    fake = _FakeRustClient()
    client._rust_client = fake
    return fake


class TestNanonisTCPClient:
    """Tests for NanonisTCPClient."""
    
    def test_init(self):
        """Test client initialization."""
        client = NanonisTCPClient('127.0.0.1', 6501)
        assert client.host == '127.0.0.1'
        assert client.port == 6501
        assert client.timeout == 10.0
        assert not client.is_connected
    
    def test_init_custom_timeout(self):
        """Test client with custom timeout."""
        client = NanonisTCPClient('127.0.0.1', 6501, timeout=5.0)
        assert client.timeout == 5.0
    
    @patch('socket.socket')
    def test_connect_success(self, mock_socket_class):
        """Test successful connection."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = NanonisTCPClient('127.0.0.1', 6501)
        rust_client = _attach_fake_rust_client(client)
        client.connect()
        
        if rust_client:
            rust_client.connect.assert_called_once_with()
            mock_socket_class.assert_not_called()
        else:
            mock_socket.settimeout.assert_called_once_with(10.0)
            mock_socket.connect.assert_called_once_with(('127.0.0.1', 6501))
        assert client.is_connected
    
    @patch('socket.socket')
    def test_connect_failure(self, mock_socket_class):
        """Test connection failure."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_socket
        
        client = NanonisTCPClient('127.0.0.1', 6501)
        rust_client = _attach_fake_rust_client(client)
        if rust_client:
            rust_client.connect.side_effect = Exception("Connection refused")
        with pytest.raises(NanonisConnectionError):
            client.connect()
        
        if rust_client:
            mock_socket_class.assert_not_called()
        assert not client.is_connected
    
    @patch('socket.socket')
    def test_disconnect(self, mock_socket_class):
        """Test disconnection."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = NanonisTCPClient('127.0.0.1', 6501)
        rust_client = _attach_fake_rust_client(client)
        client.connect()
        client.disconnect()
        
        if rust_client:
            rust_client.disconnect.assert_called_once_with()
            mock_socket_class.assert_not_called()
        else:
            mock_socket.close.assert_called_once()
        assert not client.is_connected
    
    def test_encode_header(self):
        """Test header encoding."""
        client = NanonisTCPClient('127.0.0.1', 6501)
        header = client._encode_header('Bias.Get', 0)
        
        assert len(header) == 40
        assert header[:8] == b'Bias.Get'
        assert header[32:36] == b'\x00\x00\x00\x00'  # body size = 0
    
    def test_encode_header_with_body(self):
        """Test header encoding with body size."""
        client = NanonisTCPClient('127.0.0.1', 6501)
        header = client._encode_header('Bias.Set', 4)
        
        assert len(header) == 40
        assert header[32:36] == b'\x00\x00\x00\x04'  # body size = 4
    
    @patch('socket.socket')
    def test_context_manager(self, mock_socket_class):
        """Test context manager usage."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = NanonisTCPClient('127.0.0.1', 6501)
        rust_client = _attach_fake_rust_client(client)
        with client as client:
            assert client.is_connected
        
        if rust_client:
            rust_client.disconnect.assert_called_once_with()
            mock_socket_class.assert_not_called()
        else:
            mock_socket.close.assert_called_once()
    
    def test_repr_disconnected(self):
        """Test string representation when disconnected."""
        client = NanonisTCPClient('127.0.0.1', 6501)
        assert 'disconnected' in repr(client)
    
    @patch('socket.socket')
    def test_repr_connected(self, mock_socket_class):
        """Test string representation when connected."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = NanonisTCPClient('127.0.0.1', 6501)
        rust_client = _attach_fake_rust_client(client)
        client.connect()
        assert 'connected' in repr(client)
        if rust_client:
            assert 'backend=Rust' in repr(client)


class TestExceptions:
    """Tests for exception classes."""
    
    def test_nanonis_error(self):
        """Test base NanonisError."""
        with pytest.raises(NanonisError):
            raise NanonisError("Test error")
    
    def test_connection_error_inheritance(self):
        """Test NanonisConnectionError inherits from NanonisError."""
        with pytest.raises(NanonisError):
            raise NanonisConnectionError("Test")
    
    def test_protocol_error_inheritance(self):
        """Test NanonisProtocolError inherits from NanonisError."""
        with pytest.raises(NanonisError):
            raise NanonisProtocolError("Test")
    
    def test_timeout_error_inheritance(self):
        """Test NanonisTimeoutError inherits from NanonisError."""
        with pytest.raises(NanonisError):
            raise NanonisTimeoutError("Test")
