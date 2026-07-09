"""Focused tests for Nanonis TCP framing and stream health."""

import socket
import struct
from unittest.mock import MagicMock

import pytest

from nanonis.protocol import (
    NanonisConnectionError,
    NanonisProtocolError,
    NanonisTCPClient,
    NanonisTimeoutError,
    TransportState,
)


def response_header(command: str, body_size: int, reserved: bytes = b"\0" * 4) -> bytes:
    return command.encode().ljust(32, b"\0") + struct.pack(">i", body_size) + reserved


def connected_client(*recv_values, max_response_size=1024):
    sock = MagicMock()
    sock.gettimeout.return_value = 10.0
    sock.recv.side_effect = list(recv_values)
    client = NanonisTCPClient(
        "127.0.0.1", 6501, max_response_size=max_response_size
    )
    client._socket = sock
    client._transport_state = TransportState.READY
    return client, sock


def test_timeout_receiving_header_marks_transport_desynchronized():
    client, sock = connected_client(socket.timeout("late"))

    with pytest.raises(NanonisTimeoutError):
        client.send_raw("Bias.Get", b"")

    assert client.transport_state is TransportState.DESYNCHRONIZED
    assert not client.is_connected
    sock.close.assert_called_once()


def test_timeout_mid_body_is_timeout_not_connection_error():
    header = response_header("Bias.Get", 4)
    client, _ = connected_client(header, b"ab", socket.timeout("late"))

    with pytest.raises(NanonisTimeoutError):
        client.send_raw("Bias.Get", b"")


def test_connection_closed_mid_body_is_connection_error():
    header = response_header("Bias.Get", 4)
    client, _ = connected_client(header, b"ab", b"")

    with pytest.raises(NanonisConnectionError):
        client.send_raw("Bias.Get", b"")


@pytest.mark.parametrize(
    ("header", "message"),
    [
        (response_header("Bias.Get", -1), "negative"),
        (response_header("Bias.Get", 2048), "maximum"),
        (response_header("Bias.Set", 0), "mismatch"),
        (response_header("Bias.Get", 0, b"\0\0\0\1"), "non-zero"),
    ],
)
def test_protocol_error_on_bad_header(header, message):
    client, _ = connected_client(header)

    with pytest.raises(NanonisProtocolError, match=message):
        client.send_raw("Bias.Get", b"")

    assert client.transport_state is TransportState.DESYNCHRONIZED


def test_command_timeout_is_temporary_and_transaction_is_complete():
    header = response_header("Bias.Get", 2)
    client, sock = connected_client(header, b"ok")

    assert client.send_raw("Bias.Get", b"", timeout=45.0) == b"ok"

    assert sock.settimeout.call_args_list[0].args == (45.0,)
    assert sock.settimeout.call_args_list[-1].args == (10.0,)
    assert client.transport_state is TransportState.READY

