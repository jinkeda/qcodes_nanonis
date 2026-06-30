# -*- coding: utf-8 -*-
"""Low-level, stateful TCP framing for the Nanonis protocol."""

from __future__ import annotations

import socket
import struct
import threading
from enum import Enum
from typing import Optional

from .exceptions import (
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTimeoutError,
)


class TransportState(Enum):
    """Health of the request/response byte stream (not instrument state)."""

    DISCONNECTED = "disconnected"
    READY = "ready"
    DESYNCHRONIZED = "desynchronized"
    RECOVERING = "recovering"


class NanonisTCPClient:
    """Send complete Nanonis request/response transactions over one socket."""

    HEADER_SIZE = 40
    COMMAND_NAME_SIZE = 32
    DEFAULT_MAX_RESPONSE_SIZE = 64 * 1024 * 1024

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        max_response_size: int = DEFAULT_MAX_RESPONSE_SIZE,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if max_response_size <= 0:
            raise ValueError("max_response_size must be > 0")
        self.host = host
        self.port = port
        self.timeout = float(timeout)
        self.max_response_size = int(max_response_size)
        self._socket: Optional[socket.socket] = None
        self._io_lock = threading.RLock()
        self._transport_state = TransportState.DISCONNECTED

    @property
    def is_connected(self) -> bool:
        return self._socket is not None and self._transport_state is TransportState.READY

    @property
    def transport_state(self) -> TransportState:
        return self._transport_state

    def connect(self) -> None:
        """Establish a new stream; an existing stream is always discarded."""
        with self._io_lock:
            self._close_socket()
            self._transport_state = TransportState.RECOVERING
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
            except (socket.timeout, socket.error) as exc:
                try:
                    sock.close()
                finally:
                    self._socket = None
                    self._transport_state = TransportState.DISCONNECTED
                raise NanonisConnectionError(
                    f"Failed to connect to {self.host}:{self.port}: {exc}"
                ) from exc
            self._socket = sock
            self._transport_state = TransportState.READY

    def reconnect(self) -> None:
        """Replace the current stream with a fresh connection."""
        self.connect()

    def disconnect(self) -> None:
        with self._io_lock:
            self._close_socket()
            self._transport_state = TransportState.DISCONNECTED

    def _close_socket(self) -> None:
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except socket.error:
                pass

    def _invalidate(self) -> None:
        """Close a stream whose request/response boundary is no longer known."""
        self._close_socket()
        self._transport_state = TransportState.DESYNCHRONIZED

    def send_raw(
        self,
        command_name: str,
        body: bytes,
        *,
        timeout: float | None = None,
    ) -> bytes:
        """Send one command under the I/O lock and return its complete body."""
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be > 0 when provided")

        with self._io_lock:
            sock = self._socket
            if sock is None or self._transport_state is not TransportState.READY:
                raise NanonisConnectionError("Not connected to Nanonis")

            previous_timeout = sock.gettimeout()
            command_timeout = self.timeout if timeout is None else float(timeout)
            try:
                sock.settimeout(command_timeout)
                header = self._encode_header(command_name, len(body))
                try:
                    sock.sendall(header + body)
                except socket.timeout as exc:
                    raise NanonisTimeoutError("Request send timed out") from exc
                except socket.error as exc:
                    raise NanonisConnectionError(
                        f"Failed to send command: {exc}"
                    ) from exc
                response = self._receive_response(command_name)
                self._transport_state = TransportState.READY
                return response
            except (NanonisTimeoutError, NanonisConnectionError, NanonisProtocolError):
                self._invalidate()
                raise
            finally:
                # Do not touch a closed/invalidated socket. A healthy socket gets its
                # prior timeout back before another thread can acquire the lock.
                if self._socket is sock:
                    sock.settimeout(previous_timeout)

    def _encode_header(self, command_name: str, body_size: int) -> bytes:
        encoded = command_name.encode("utf-8")
        if len(encoded) > self.COMMAND_NAME_SIZE:
            raise ValueError("command name exceeds 32 encoded bytes")
        if body_size < 0:
            raise ValueError("body_size must be non-negative")
        command = encoded.ljust(self.COMMAND_NAME_SIZE, b"\x00")
        return command + struct.pack(">iHH", body_size, 1, 0)

    def _receive_response(self, expected_command: str) -> bytes:
        try:
            header = self._recv_exact(self.HEADER_SIZE)
            raw_command = header[: self.COMMAND_NAME_SIZE]
            try:
                command = raw_command.split(b"\x00", 1)[0].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise NanonisProtocolError(
                    "Response command name is not valid UTF-8"
                ) from exc
            if b"\x00" in raw_command:
                padding = raw_command[raw_command.index(b"\x00") :]
                if padding.strip(b"\x00"):
                    raise NanonisProtocolError(
                        "Response command-name padding contains non-zero bytes"
                    )

            body_size = struct.unpack(">i", header[32:36])[0]
            reserved = header[36:40]
            if command != expected_command:
                raise NanonisProtocolError(
                    f"Response command mismatch: expected {expected_command!r}, "
                    f"received {command!r}"
                )
            if body_size < 0:
                raise NanonisProtocolError(
                    f"Response body size is negative: {body_size}"
                )
            if body_size > self.max_response_size:
                raise NanonisProtocolError(
                    f"Response body size {body_size} exceeds configured maximum "
                    f"{self.max_response_size}"
                )
            # The protocol manual defines all four response-header bytes as unused.
            if reserved != b"\x00\x00\x00\x00":
                raise NanonisProtocolError(
                    f"Response reserved header bytes are non-zero: {reserved!r}"
                )
            return self._recv_exact(body_size) if body_size else b""
        except socket.timeout as exc:
            raise NanonisTimeoutError("Response timed out") from exc

    def _recv_exact(self, size: int) -> bytes:
        sock = self._socket
        if sock is None:
            raise NanonisConnectionError("Socket is not connected")
        chunks: list[bytes] = []
        received = 0
        while received < size:
            try:
                chunk = sock.recv(size - received)
            except socket.timeout:
                # Preserve the category so _receive_response can classify it.
                raise
            except socket.error as exc:
                raise NanonisConnectionError(f"Receive failed: {exc}") from exc
            if not chunk:
                raise NanonisConnectionError(
                    f"Connection closed while receiving data "
                    f"(got {received}/{size} bytes)"
                )
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)

    def __enter__(self) -> "NanonisTCPClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def __repr__(self) -> str:
        status = (
            "connected (ready)"
            if self.transport_state is TransportState.READY
            else self.transport_state.value
        )
        return (
            f"NanonisTCPClient({self.host}:{self.port}, "
            f"{status})"
        )
