# -*- coding: utf-8 -*-
"""
Nanonis Protocol Exceptions

Custom exceptions for the Nanonis TCP communication layer.
"""


class NanonisError(Exception):
    """Base exception for all Nanonis-related errors."""
    pass


class NanonisConnectionError(NanonisError):
    """Raised when connection to Nanonis fails."""
    pass


class NanonisProtocolError(NanonisError):
    """Raised when a protocol-level error occurs (malformed response, etc.)."""
    pass


class NanonisTimeoutError(NanonisError):
    """Raised when a command times out."""
    pass


class NanonisCommandError(NanonisError):
    """Raised when a command fails on the Nanonis side."""
    
    def __init__(self, command: str, message: str):
        self.command = command
        super().__init__(f"Command '{command}' failed: {message}")
