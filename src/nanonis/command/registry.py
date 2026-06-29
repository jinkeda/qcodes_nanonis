# -*- coding: utf-8 -*-
"""
Command Registry

Loads and manages command definitions for the Nanonis TCP protocol.

The canonical source of truth is the per-module command files in
``configs/commands/*.json`` (raw protocol form: ``args``/``resp`` with short
type codes such as ``i`` / ``s`` / ``1D array int``). The registry converts
these to the codec's readable types at load time, so no separate generated
YAML is required. YAML loading is still supported for the pre-generated
``nanonis_tcp.yaml`` (already-converted form).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import yaml


# --- Raw JSON -> codec type conversion --------------------------------------
# Short type codes used in configs/commands/*.json mapped to the readable types
# understood by CommandEncoder/CommandDecoder.
TYPE_MAPPING = {
    # Scalars
    'f': 'float32',
    'd': 'float64',
    'i': 'int32',
    'I': 'uint32',
    'H': 'uint16',
    'h': 'int16',
    's': 'string',
    # Arrays (spelled out in the JSON)
    '1D array float32': 'array_float32',
    '1D array float64': 'array_float64',
    '1D array int': 'array_int32',
    '1D array int32': 'array_int32',
    '1D array string': 'array_string',
    '2D array float32': 'matrix_float32',
    '2D array string': 'matrix_string',
}

_INT_TYPES = {'int16', 'int32', 'uint16', 'uint32'}


def sanitize_name(name: str) -> str:
    """Convert a raw argument name into a snake_case Python-friendly identifier."""
    name = name.replace('-', '_').replace(' ', '_').replace('/', '_').replace('.', '_')
    name = re.sub(r'\(([^)]+)\)', r'_\1', name)       # keep unit hints e.g. (V)
    name = re.sub(r'[^a-zA-Z0-9_]', '', name).lower()
    name = re.sub(r'_+', '_', name).strip('_')
    name = name.replace('number_of_', 'num_')
    return name or 'unnamed'


def map_type(type_str: str) -> str:
    """Map a JSON short type code to the codec's readable type."""
    if type_str in TYPE_MAPPING:
        return TYPE_MAPPING[type_str]
    for key, value in TYPE_MAPPING.items():
        if type_str.lower() == key.lower():
            return value
    return f'UNKNOWN:{type_str}'


def normalize_size_fields(args: List[dict]) -> List[dict]:
    """
    Drop the redundant byte-size field that precedes each *scalar* string.

    The protocol PDF lists a scalar string as ``<x> size`` (int) then ``<x>``
    (string), but on the wire a body string is ``[int32 length][chars]`` - the
    "size" *is* the string's own length prefix. The ``string`` codec is
    self-describing, so a separate ``<x> size`` field is redundant and would
    corrupt the byte stream. String *arrays* are left untouched: their byte-size
    and element-count are independent, real wire fields.
    """
    def is_size_marker(arg: dict) -> bool:
        return 'size' in arg['name'].lower() and (
            arg['type'] in _INT_TYPES or arg['type'] == 'string'
        )

    out: List[dict] = []
    for arg in args:
        if arg['type'] == 'string' and out and is_size_marker(out[-1]):
            out.pop()
        out.append(arg)
    return out


def convert_raw_args(raw_args: List[dict]) -> List[dict]:
    """Convert raw JSON ``args``/``resp`` entries to normalized codec args."""
    converted = [
        {
            'name': sanitize_name(a['name']),
            'type': map_type(a['type']),
            'original_name': a['name'],
        }
        for a in raw_args or []
    ]
    return normalize_size_fields(converted)


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
        Load command definitions from a raw protocol JSON file.

        This is the per-module form in ``configs/commands/*.json``: each command
        uses ``args``/``resp`` with short type codes (``i``, ``s``,
        ``1D array int`` ...). Types are mapped to the codec's readable types and
        redundant scalar-string size fields are normalized away at load time.

        Args:
            path: Path to a raw JSON command file
        """
        import json

        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for name, cmd_data in data.items():
            converted = {
                'send': convert_raw_args(cmd_data.get('args', [])),
                'recv': convert_raw_args(cmd_data.get('resp', [])),
            }
            self._commands[name] = CommandDefinition.from_dict(name, converted)

    def load_from_dir(self, path: Union[str, Path], pattern: str = '*.json') -> None:
        """
        Load command definitions from a directory of raw protocol JSON files.

        Every ``*.json`` file in the directory is loaded via
        :meth:`load_from_json`, so the whole ``configs/commands/`` folder can be
        used directly as the runtime command source (no generated YAML needed).

        Args:
            path: Path to the directory of per-module command files
            pattern: Glob pattern for command files (default ``*.json``)
        """
        path = Path(path)
        files = sorted(path.glob(pattern))
        if not files:
            raise FileNotFoundError(
                f"No command files matching '{pattern}' found in {path}"
            )
        for file in files:
            self.load_from_json(file)
    
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
