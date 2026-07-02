# -*- coding: utf-8 -*-
"""
Nanonis Controller

Main command interface for communicating with Nanonis.
Orchestrates the registry, encoder, and TCP client.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..protocol import NanonisTCPClient, TransportState
from .registry import CommandRegistry
from .encoder import CommandEncoder, CommandDecoder
from .validation import CommandArgumentValidator

logger = logging.getLogger(__name__)


class NanonisController:
    """
    Layer 2: Main command interface for Nanonis.
    
    This is the primary entry point for sending commands to Nanonis.
    It combines the TCP client, command registry, and encoder/decoder.
    
    Features:
    - Configuration-driven command dispatch
    - Automatic type coercion
    - Error detection from Nanonis responses
    - Debug mode for verbose logging
    
    Example (standalone):
        >>> with NanonisController('127.0.0.1', 6501, 'configs/commands') as ctrl:
        ...     ctrl.send('Bias.Set', 0.5)
        ...     voltage = ctrl.send('Bias.Get')
        ...     print(f"Bias: {voltage} V")
    
    Example (with debug mode):
        >>> ctrl = NanonisController('127.0.0.1', 6501, 'configs/commands')
        >>> ctrl.debug = True  # Enable verbose logging
        >>> ctrl.connect()
        >>> ctrl.send('Bias.Get')
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        config_path: Optional[Union[str, Path]] = None,
        timeout: float = 10.0,
        debug: bool = False,
    ):
        """
        Initialize the controller.
        
        Args:
            host: Nanonis host IP address
            port: Nanonis TCP port (typically 6501)
            config_path: Optional path to a directory of per-module JSON files
            timeout: Socket timeout in seconds
            debug: Enable debug mode for verbose logging
        """
        self._client = NanonisTCPClient(host, port, timeout)
        self._registry = CommandRegistry()
        self._debug = debug
        self._encoder = CommandEncoder(debug=debug)
        self._decoder = CommandDecoder(debug=debug)
        self._argument_validator = CommandArgumentValidator()
        
        if config_path:
            self.load_config(config_path)
    
    @property
    def debug(self) -> bool:
        """Get debug mode status."""
        return self._debug
    
    @debug.setter
    def debug(self, value: bool) -> None:
        """
        Set debug mode.
        
        When enabled, logs detailed information about:
        - Type coercion during encoding
        - Bytes sent/received
        - Decoded values
        - Any errors from Nanonis
        """
        self._debug = value
        self._encoder.debug = value
        self._decoder.debug = value
        
        if value:
            # Set logging level to DEBUG for our logger
            logging.getLogger('nanonis').setLevel(logging.DEBUG)
            logger.info("Debug mode enabled")
    
    def load_config(self, path: Union[str, Path]) -> None:
        """
        Load command configuration.

        The command directory is the sole runtime source of command definitions.

        Args:
            path: Path to a directory of per-module JSON command files
        """
        path = Path(path)
        if not path.is_dir():
            raise ValueError(f"Command config must be a directory: {path}")
        self._registry.load_from_dir(path)

        if self._debug:
            logger.info(f"Loaded {len(self._registry)} commands from {path}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Nanonis."""
        return self._client.is_connected

    @property
    def transport_state(self) -> TransportState:
        """Return byte-stream health without implying instrument state."""
        return self._client.transport_state
    
    def connect(self) -> None:
        """Establish connection to Nanonis."""
        self._client.connect()
        if self._debug:
            logger.info(f"Connected to {self._client.host}:{self._client.port}")
    
    def disconnect(self) -> None:
        """Close connection to Nanonis."""
        self._client.disconnect()
        if self._debug:
            logger.info("Disconnected")

    def reconnect(self) -> None:
        """Discard the current byte stream and establish a fresh one."""
        self._client.reconnect()
        if self._debug:
            logger.info("Reconnected")
    
    def send(
        self,
        command: str,
        *args: Any,
        timeout: float | None = None,
        check_error: bool = True,
    ) -> Any:
        """
        Send a command to Nanonis.
        
        Args:
            command: Command name (e.g., 'Bias.Set', 'Scan.FrameGet')
            *args: Command arguments in order
            check_error: Whether to check for Nanonis errors in response
            
        Returns:
            - None: If command has no return values
            - Single value: If command has one return value
            - Dict: If command has multiple return values
            
        Raises:
            KeyError: If command not found in registry
            ValueError: If argument encoding fails
            NanonisConnectionError: If not connected
            NanonisCommandError: If Nanonis returned an error
        """
        if self._debug:
            logger.debug(f"Sending: {command}{args}")
        
        # Get command definition
        cmd_def = self._registry.get(command)
        
        # Encode arguments (with type coercion)
        send_types = cmd_def.get_send_types()
        validated_args = self._argument_validator.validate_positional(cmd_def, args)
        body = self._encoder.encode(send_types, validated_args)
        
        if self._debug:
            logger.debug(f"Request body: {len(body)} bytes")
        
        # Send command and get response
        if timeout is None:
            response = self._client.send_raw(command, body)
        else:
            response = self._client.send_raw(command, body, timeout=timeout)
        
        if self._debug:
            logger.debug(f"Response: {len(response)} bytes")
        
        # Decode response (with error checking)
        if not cmd_def.recv_args:
            self._decoder.decode(
                [], response, check_error=check_error, command_name=command
            )
            return None
        
        recv_types = cmd_def.get_recv_types()
        result = self._decoder.decode(
            recv_types,
            response,
            check_error=check_error,
            command_name=command,
            constraints=cmd_def.recv_constraints,
        )
        
        # Return single value or dict
        if len(result) == 1:
            return list(result.values())[0]
        return result

    def send_fields(
        self,
        command: str,
        /,
        *,
        timeout: float | None = None,
        check_error: bool = True,
        **fields: Any,
    ) -> Any:
        """Send a command by sanitized field name, inferring derived sizes."""
        cmd_def = self._registry.get(command)
        args = self._argument_validator.materialize_named(cmd_def, fields)
        return self.send(
            command,
            *args,
            timeout=timeout,
            check_error=check_error,
        )
    
    def send_raw(
        self,
        command: str,
        body: bytes,
        *,
        timeout: float | None = None,
    ) -> bytes:
        """
        Send a raw command without encoding/decoding.
        
        Useful for debugging or custom commands not in the registry.
        
        Args:
            command: Command name
            body: Raw body bytes
            
        Returns:
            Raw response bytes
        """
        if self._debug:
            logger.debug(f"Raw send: {command}, {len(body)} bytes")
        if timeout is None:
            return self._client.send_raw(command, body)
        return self._client.send_raw(command, body, timeout=timeout)
    
    def list_commands(self, prefix: str = '') -> List[str]:
        """
        List available commands.
        
        Args:
            prefix: Optional filter prefix (e.g., 'Bias.')
            
        Returns:
            List of command names
        """
        return self._registry.list_commands(prefix)
    
    def list_modules(self) -> List[str]:
        """
        List available command modules.
        
        Returns:
            List of module names (e.g., ['Bias', 'Scan', 'ZCtrl'])
        """
        return self._registry.list_modules()
    
    def get_command_info(self, command: str) -> Dict[str, Any]:
        """
        Get detailed information about a command.
        
        Args:
            command: Command name
            
        Returns:
            Dictionary with command details
        """
        cmd_def = self._registry.get(command)
        return {
            'name': cmd_def.name,
            'send_args': [(a.name, a.type) for a in cmd_def.send_args],
            'recv_args': [(a.name, a.type) for a in cmd_def.recv_args],
            'send_constraints': {
                name: vars(value)
                for name, value in cmd_def.send_constraints.items()
            },
            'recv_constraints': {
                name: vars(value)
                for name, value in cmd_def.recv_constraints.items()
            },
        }
    
    def __enter__(self) -> 'NanonisController':
        """Context manager entry: connect."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: disconnect."""
        self.disconnect()
    
    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        debug_str = ", debug" if self._debug else ""
        return f"NanonisController({self._client.host}:{self._client.port}, {status}, {len(self._registry)} commands{debug_str})"
