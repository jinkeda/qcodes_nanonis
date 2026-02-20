# -*- coding: utf-8 -*-
"""
Command Registry

Loads and manages command definitions from YAML configuration.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import yaml


@dataclass
class ArgDefinition:
    """Definition of a single argument."""
    name: str
    type: str
    original_name: str = ''
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ArgDefinition':
        return cls(
            name=data.get('name', 'unnamed'),
            type=data.get('type', 'unknown'),
            original_name=data.get('original_name', ''),
        )


@dataclass
class CommandDefinition:
    """Definition of a Nanonis command."""
    name: str
    send_args: List[ArgDefinition] = field(default_factory=list)
    recv_args: List[ArgDefinition] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'CommandDefinition':
        send_args = [ArgDefinition.from_dict(a) for a in data.get('send', [])]
        recv_args = [ArgDefinition.from_dict(a) for a in data.get('recv', [])]
        return cls(name=name, send_args=send_args, recv_args=recv_args)
    
    def get_send_types(self) -> List[Tuple[str, str]]:
        """Get list of (name, type) tuples for send arguments."""
        return [(a.name, a.type) for a in self.send_args]
    
    def get_recv_types(self) -> List[Tuple[str, str]]:
        """Get list of (name, type) tuples for receive arguments."""
        return [(a.name, a.type) for a in self.recv_args]


class CommandRegistry:
    """
    Registry of all available Nanonis commands.
    
    Loads command definitions from YAML and provides lookup.
    
    Example:
        >>> registry = CommandRegistry()
        >>> registry.load_from_yaml('configs/nanonis_tcp.yaml')
        >>> cmd = registry.get('Bias.Set')
        >>> print(cmd.send_args)
    """
    
    def __init__(self):
        self._commands: Dict[str, CommandDefinition] = {}
    
    def load_from_yaml(self, path: Union[str, Path]) -> None:
        """
        Load command definitions from a YAML file.
        
        Args:
            path: Path to the YAML configuration file
        """
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            return
        
        for name, cmd_data in data.items():
            if isinstance(cmd_data, dict):
                self._commands[name] = CommandDefinition.from_dict(name, cmd_data)
    
    def load_from_json(self, path: Union[str, Path]) -> None:
        """
        Load command definitions from a JSON file (legacy format).
        
        Args:
            path: Path to the JSON configuration file
        """
        import json
        
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON format uses 'args' and 'resp' instead of 'send' and 'recv'
        for name, cmd_data in data.items():
            converted = {
                'send': cmd_data.get('args', []),
                'recv': cmd_data.get('resp', []),
            }
            self._commands[name] = CommandDefinition.from_dict(name, converted)
    
    def get(self, name: str) -> CommandDefinition:
        """
        Get a command definition by name.
        
        Args:
            name: Command name (e.g., 'Bias.Set')
            
        Returns:
            CommandDefinition for the command
            
        Raises:
            KeyError: If command not found
        """
        if name not in self._commands:
            raise KeyError(f"Unknown command: '{name}'")
        return self._commands[name]
    
    def has(self, name: str) -> bool:
        """Check if a command exists."""
        return name in self._commands
    
    def list_commands(self, prefix: str = '') -> List[str]:
        """
        List available commands, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter commands (e.g., 'Bias.')
            
        Returns:
            List of command names
        """
        if prefix:
            return sorted([n for n in self._commands if n.startswith(prefix)])
        return sorted(self._commands.keys())
    
    def list_modules(self) -> List[str]:
        """
        List available command modules (prefixes before the first dot).
        
        Returns:
            Sorted list of module names
        """
        modules = set()
        for name in self._commands:
            if '.' in name:
                modules.add(name.split('.')[0])
        return sorted(modules)
    
    def __len__(self) -> int:
        return len(self._commands)
    
    def __contains__(self, name: str) -> bool:
        return name in self._commands
    
    def __repr__(self) -> str:
        return f"CommandRegistry({len(self._commands)} commands)"
