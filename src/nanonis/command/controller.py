# -*- coding: utf-8 -*-
"""
Nanonis Controller

Main command interface for communicating with Nanonis.
Orchestrates the registry, encoder, and TCP client.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..protocol import NanonisTCPClient
from .registry import CommandRegistry
from .encoder import CommandEncoder, CommandDecoder

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
        >>> with NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml') as ctrl:
        ...     ctrl.send('Bias.Set', 0.5)
        ...     voltage = ctrl.send('Bias.Get')
        ...     print(f"Bias: {voltage} V")
    
    Example (with debug mode):
        >>> ctrl = NanonisController('127.0.0.1', 6501, 'config.yaml')
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
            config_path: Optional path to YAML/JSON config file
            timeout: Socket timeout in seconds
            debug: Enable debug mode for verbose logging
        """
        self._client = NanonisTCPClient(host, port, timeout)
        self._registry = CommandRegistry()
        self._debug = debug
        self._encoder = CommandEncoder(debug=debug)
        self._decoder = CommandDecoder(debug=debug)
        
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
        Load command configuration from file.
        
        Args:
            path: Path to YAML or JSON config file
        """
        path = Path(path)
        if path.suffix in ('.yaml', '.yml'):
            self._registry.load_from_yaml(path)
        else:
            self._registry.load_from_json(path)
        
        if self._debug:
            logger.info(f"Loaded {len(self._registry)} commands from {path}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Nanonis."""
        return self._client.is_connected
    
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
    
    def send(self, command: str, *args, check_error: bool = True) -> Any:
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
        body = self._encoder.encode(send_types, args)
        
        if self._debug:
            logger.debug(f"Request body: {len(body)} bytes")
        
        # Send command and get response
        response = self._client.send_raw(command, body)
        
        if self._debug:
            logger.debug(f"Response: {len(response)} bytes")
        
        # Decode response (with error checking)
        if not cmd_def.recv_args:
            # Even commands with no return values can have errors
            if check_error and len(response) >= 8:
                self._decoder._parse_error(response)
            return None
        
        recv_types = cmd_def.get_recv_types()
        result = self._decoder.decode(recv_types, response, check_error=check_error)
        
        # Return single value or dict
        if len(result) == 1:
            return list(result.values())[0]
        return result
    
    def send_raw(self, command: str, body: bytes) -> bytes:
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
        return self._client.send_raw(command, body)
    
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
