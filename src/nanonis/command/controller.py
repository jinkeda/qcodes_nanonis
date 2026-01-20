# -*- coding: utf-8 -*-
"""
Nanonis Controller

Main command interface for communicating with Nanonis.
Orchestrates the registry, encoder, and TCP client.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..protocol import NanonisTCPClient
from .registry import CommandRegistry
from .encoder import CommandEncoder, CommandDecoder


class NanonisController:
    """
    Layer 2: Main command interface for Nanonis.
    
    This is the primary entry point for sending commands to Nanonis.
    It combines the TCP client, command registry, and encoder/decoder.
    
    Example (standalone):
        >>> with NanonisController('127.0.0.1', 6501, 'configs/nanonis_tcp.yaml') as ctrl:
        ...     ctrl.send('Bias.Set', 0.5)
        ...     voltage = ctrl.send('Bias.Get')
        ...     print(f"Bias: {voltage} V")
    
    Example (manual connection):
        >>> ctrl = NanonisController('127.0.0.1', 6501)
        >>> ctrl.load_config('configs/nanonis_tcp.yaml')
        >>> ctrl.connect()
        >>> try:
        ...     ctrl.send('Bias.Set', 0.5)
        ... finally:
        ...     ctrl.disconnect()
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        config_path: Optional[Union[str, Path]] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize the controller.
        
        Args:
            host: Nanonis host IP address
            port: Nanonis TCP port (typically 6501)
            config_path: Optional path to YAML/JSON config file
            timeout: Socket timeout in seconds
        """
        self._client = NanonisTCPClient(host, port, timeout)
        self._registry = CommandRegistry()
        self._encoder = CommandEncoder()
        self._decoder = CommandDecoder()
        
        if config_path:
            self.load_config(config_path)
    
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
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Nanonis."""
        return self._client.is_connected
    
    def connect(self) -> None:
        """Establish connection to Nanonis."""
        self._client.connect()
    
    def disconnect(self) -> None:
        """Close connection to Nanonis."""
        self._client.disconnect()
    
    def send(self, command: str, *args) -> Any:
        """
        Send a command to Nanonis.
        
        Args:
            command: Command name (e.g., 'Bias.Set', 'Scan.FrameGet')
            *args: Command arguments in order
            
        Returns:
            - None: If command has no return values
            - Single value: If command has one return value
            - Dict: If command has multiple return values
            
        Raises:
            KeyError: If command not found in registry
            ValueError: If argument encoding fails
            NanonisConnectionError: If not connected
        """
        # Get command definition
        cmd_def = self._registry.get(command)
        
        # Encode arguments
        send_types = cmd_def.get_send_types()
        body = self._encoder.encode(send_types, args)
        
        # Send command and get response
        response = self._client.send_raw(command, body)
        
        # Decode response
        if not cmd_def.recv_args:
            return None
        
        recv_types = cmd_def.get_recv_types()
        result = self._decoder.decode(recv_types, response)
        
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
        return f"NanonisController({self._client.host}:{self._client.port}, {status}, {len(self._registry)} commands)"
