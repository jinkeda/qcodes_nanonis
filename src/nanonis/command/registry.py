# -*- coding: utf-8 -*-
"""
Command Registry

Loads and manages command definitions for the Nanonis TCP protocol.

The canonical source of truth is the per-module command files in
``configs/commands/*.json`` (raw protocol form: ``args``/``resp`` with short
type codes such as ``i`` / ``s`` / ``1D array int``). The registry converts
these to the codec's readable types at load time.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Tuple, Union


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
    '1D array unsigned int32': 'array_uint32',
    '1D array unsigned int8': 'array_uint8',
    '1D array string': 'array_string',
    '2D array float32': 'matrix_float32',
    '2D array string': 'matrix_string',
}

_INT_TYPES = {'int16', 'int32', 'uint16', 'uint32'}
NAMED_SEND_CONTROL_FIELDS = frozenset({'_timeout', '_check_error'})


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


@dataclass(frozen=True)
class VariableLengthConstraint:
    """Explicit sizing relationship for one array or matrix field."""

    field: str
    count: str | None = None
    byte_size: str | None = None
    rows: str | None = None
    columns: str | None = None

    @classmethod
    def from_dict(cls, field_name: str, data: Mapping[str, object]) -> 'VariableLengthConstraint':
        allowed = {'count', 'byte_size', 'rows', 'columns'}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(
                f"Constraint for {field_name!r} has unknown keys: {sorted(unknown)}"
            )
        return cls(
            field=field_name,
            count=_optional_string(data.get('count'), 'count', field_name),
            byte_size=_optional_string(data.get('byte_size'), 'byte_size', field_name),
            rows=_optional_string(data.get('rows'), 'rows', field_name),
            columns=_optional_string(data.get('columns'), 'columns', field_name),
        )


def _optional_string(value: object, key: str, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"Constraint {key!r} for {field_name!r} must be a non-empty string"
        )
    return value


@dataclass
class CommandDefinition:
    """Definition of a Nanonis command."""
    name: str
    send_args: List[ArgDefinition] = field(default_factory=list)
    recv_args: List[ArgDefinition] = field(default_factory=list)
    send_constraints: Dict[str, VariableLengthConstraint] = field(default_factory=dict)
    recv_constraints: Dict[str, VariableLengthConstraint] = field(default_factory=dict)
    
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
    
    Loads command definitions from per-module JSON files and provides lookup.
    
    Example:
        >>> registry = CommandRegistry()
        >>> registry.load_from_dir('configs/commands')
        >>> cmd = registry.get('Bias.Set')
        >>> print(cmd.send_args)
    """
    
    def __init__(self):
        self._commands: Dict[str, CommandDefinition] = {}
    
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
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for name, cmd_data in data.items():
            converted = {
                'send': convert_raw_args(cmd_data.get('args', [])),
                'recv': convert_raw_args(cmd_data.get('resp', [])),
            }
            self._validate_unique_names(name, 'send', converted['send'])
            self._validate_unique_names(name, 'recv', converted['recv'])
            self._commands[name] = CommandDefinition.from_dict(name, converted)

    def load_from_dir(
        self,
        path: Union[str, Path],
        pattern: str = '*.json',
        *,
        require_constraints: bool = True,
    ) -> None:
        """
        Load command definitions from a directory of raw protocol JSON files.

        Every ``*.json`` file in the directory is loaded via
        :meth:`load_from_json`, so the whole ``configs/commands/`` folder can be
        used directly as the runtime command source (no generated YAML needed).

        Args:
            path: Path to the directory of per-module command files
            pattern: Glob pattern for command files (default ``*.json``)
            require_constraints: Reject a variable-length catalog when its
                constraints overlay is absent. Set false only for legacy or
                deliberately unconstrained custom schemas.
        """
        path = Path(path)
        files = sorted(path.glob(pattern))
        if not files:
            raise FileNotFoundError(
                f"No command files matching '{pattern}' found in {path}"
            )
        for file in files:
            self.load_from_json(file)

        self._validate_named_send_controls()

        overlay = path.parent / 'command_constraints.json'
        if overlay.is_file():
            self.load_constraints(overlay)
        elif require_constraints and self._has_variable_fields():
            raise FileNotFoundError(
                f"Variable-length command catalog requires constraint overlay: "
                f"{overlay}. Pass require_constraints=False only to load an "
                f"intentionally unconstrained custom catalog."
            )

    def _has_variable_fields(self) -> bool:
        return any(
            arg.type.startswith('array_') or arg.type.startswith('matrix_')
            for command in self._commands.values()
            for arg in (*command.send_args, *command.recv_args)
        )

    def _validate_named_send_controls(self) -> None:
        collisions = {
            command.name: sorted(
                {arg.name for arg in command.send_args} & NAMED_SEND_CONTROL_FIELDS
            )
            for command in self._commands.values()
        }
        collisions = {name: fields for name, fields in collisions.items() if fields}
        if collisions:
            raise ValueError(
                f"Command fields collide with send_fields controls: {collisions}"
            )

    @staticmethod
    def _validate_unique_names(command: str, side: str, args: List[dict]) -> None:
        names = [arg['name'] for arg in args]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                f"{command} {side} fields are not unique after sanitization: "
                f"{duplicates}"
            )

    def load_constraints(self, path: Union[str, Path]) -> None:
        """Load and validate the curated variable-length constraint overlay."""
        path = Path(path)
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError("Command constraints must be a JSON object")

        for command_name, command_payload in data.items():
            if command_name not in self._commands:
                raise ValueError(
                    f"Constraint overlay references unknown command {command_name!r}"
                )
            if not isinstance(command_payload, dict):
                raise ValueError(f"Constraints for {command_name} must be an object")
            unknown_sides = set(command_payload) - {'send', 'recv'}
            if unknown_sides:
                raise ValueError(
                    f"Constraints for {command_name} have unknown sides: "
                    f"{sorted(unknown_sides)}"
                )
            definition = self._commands[command_name]
            for side in ('send', 'recv'):
                payload = command_payload.get(side)
                if payload is None:
                    continue
                constraints = self._parse_side_constraints(
                    command_name,
                    side,
                    payload,
                    definition.send_args if side == 'send' else definition.recv_args,
                )
                if side == 'send':
                    definition.send_constraints = constraints
                else:
                    definition.recv_constraints = constraints

        self._validate_catalog_coverage('send')
        self._validate_catalog_coverage('recv')

    def _parse_side_constraints(
        self,
        command: str,
        side: str,
        payload: object,
        args: List[ArgDefinition],
    ) -> Dict[str, VariableLengthConstraint]:
        if not isinstance(payload, dict):
            raise ValueError(f"{command} {side} constraints must be an object")
        fields = {arg.name: arg for arg in args}
        constraints: Dict[str, VariableLengthConstraint] = {}
        for field_name, raw_constraint in payload.items():
            if field_name not in fields:
                raise ValueError(
                    f"{command} {side} constraint references unknown field "
                    f"{field_name!r}"
                )
            if not isinstance(raw_constraint, dict):
                raise ValueError(
                    f"Constraint for {command} {side} {field_name} must be an object"
                )
            arg_type = fields[field_name].type
            if not (arg_type.startswith('array_') or arg_type.startswith('matrix_')):
                raise ValueError(
                    f"Constraint target {command} {side} {field_name} is not an array"
                )
            constraint = VariableLengthConstraint.from_dict(
                field_name, raw_constraint
            )
            refs = [
                value
                for value in (
                    constraint.count,
                    constraint.byte_size,
                    constraint.rows,
                    constraint.columns,
                )
                if value is not None
            ]
            for reference in refs:
                if reference not in fields:
                    raise ValueError(
                        f"{command} {side} constraint for {field_name!r} "
                        f"references unknown field {reference!r}"
                    )
                if fields[reference].type not in _INT_TYPES:
                    raise ValueError(
                        f"{command} {side} size field {reference!r} is not integer"
                    )
            if arg_type.startswith('array_'):
                if constraint.count is None or constraint.rows or constraint.columns:
                    raise ValueError(
                        f"{command} {side} array {field_name!r} requires count only"
                    )
            else:
                if constraint.rows is None or constraint.columns is None or constraint.count:
                    raise ValueError(
                        f"{command} {side} matrix {field_name!r} requires rows and columns"
                    )
            if constraint.byte_size and arg_type != 'array_string':
                raise ValueError(
                    f"{command} {side} byte_size is only valid for string arrays"
                )
            constraints[field_name] = constraint

        variable_fields = {
            arg.name
            for arg in args
            if arg.type.startswith('array_') or arg.type.startswith('matrix_')
        }
        if constraints and set(constraints) != variable_fields:
            missing = sorted(variable_fields - set(constraints))
            extra = sorted(set(constraints) - variable_fields)
            raise ValueError(
                f"{command} {side} constraints must cover the whole side; "
                f"missing={missing}, extra={extra}"
            )
        return constraints

    def _validate_catalog_coverage(self, side: str) -> None:
        missing: List[str] = []
        for command in self._commands.values():
            args = command.send_args if side == 'send' else command.recv_args
            constraints = (
                command.send_constraints if side == 'send' else command.recv_constraints
            )
            if any(
                arg.type.startswith('array_') or arg.type.startswith('matrix_')
                for arg in args
            ) and not constraints:
                missing.append(command.name)
        if missing:
            raise ValueError(
                f"Constraint overlay does not cover {side} arrays for: "
                f"{', '.join(sorted(missing))}"
            )
    
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
