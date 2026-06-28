#!/usr/bin/env python3
"""
Convert nanonis_tcp_auto.json to nanonis_tcp.yaml

This script:
1. Loads the auto-generated JSON command definitions
2. Sanitizes argument names (e.g., "Bias value (V)" -> "bias_voltage")
3. Maps short type codes to readable types
4. Outputs a clean YAML configuration file
"""

import json
import re
from pathlib import Path
import yaml


# Type mapping from short codes to readable types
TYPE_MAPPING = {
    # Scalar types
    'f': 'float32',
    'd': 'float64',
    'i': 'int32',
    'I': 'uint32',
    'H': 'uint16',
    'h': 'int16',
    's': 'string',
    # Array types (from JSON strings)
    '1D array float32': 'array_float32',
    '1D array float64': 'array_float64',
    '1D array int': 'array_int32',
    '1D array int32': 'array_int32',
    '1D array string': 'array_string',
    '2D array float32': 'matrix_float32',
    '2D array string': 'matrix_string',
}


def sanitize_name(name: str) -> str:
    """
    Convert argument names to valid Python identifiers.
    
    Examples:
        "Bias value (V)" -> "bias_voltage_v"
        "Z-Controller status" -> "z_controller_status"
        "Number of channels" -> "num_channels"
    """
    # Common replacements
    name = name.replace('-', '_')
    name = name.replace(' ', '_')
    name = name.replace('/', '_')
    name = name.replace('.', '_')
    
    # Remove parentheses content but keep unit hints
    name = re.sub(r'\(([^)]+)\)', r'_\1', name)
    
    # Remove special characters
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Replace common long phrases
    name = name.replace('number_of_', 'num_')
    
    return name or 'unnamed'


_INT_TYPES = {'int16', 'int32', 'uint16', 'uint32'}


def normalize_size_fields(args: list) -> list:
    """
    Remove the redundant byte-size field that precedes each *scalar* string (RC-2).

    The Nanonis PDF lists a scalar string as two arguments - ``<x> size`` (int)
    then ``<x>`` (string) - but physically a body string is ``[int32 length]
    [chars]``, i.e. the "size" *is* the string's own length prefix. Our codec's
    ``string`` type is self-describing (it writes/reads that prefix), so the
    separate ``<x> size`` field is redundant and corrupts the byte stream if
    kept. The parser sometimes mis-maps that size field to ``string`` itself
    (e.g. ``product_line_size_int``), so both ``int`` and ``string`` size
    markers are handled.

    String *arrays* are deliberately NOT touched: per the protocol a 1D string
    array sends BOTH its size-in-bytes and its element-count as independent
    fields on the wire (in addition to each element's own length prefix), so
    those size fields are real and must be kept - the decoder consumes the
    byte-size as a field and uses the element-count (the nearest preceding int)
    as the array length. Numeric scalars and numeric arrays are untouched.

    Args:
        args: list of {'name', 'type', ...} arg dicts in wire order.

    Returns:
        A new list with the redundant scalar-string size fields removed.
    """
    def is_size_marker(arg: dict) -> bool:
        # A length-prefix field: name says "size", typed int (or mis-mapped str).
        return 'size' in arg['name'].lower() and (
            arg['type'] in _INT_TYPES or arg['type'] == 'string'
        )

    out: list = []
    for arg in args:
        if arg['type'] == 'string' and out and is_size_marker(out[-1]):
            # Scalar string self-describes: drop one preceding "* size" marker.
            out.pop()
        out.append(arg)
    return out


def map_type(type_str: str) -> str:
    """Map JSON type string to standardized type."""
    if type_str in TYPE_MAPPING:
        return TYPE_MAPPING[type_str]
    
    # Handle variations
    type_lower = type_str.lower()
    for key, value in TYPE_MAPPING.items():
        if type_lower == key.lower():
            return value
    
    # Unknown type - return as-is with warning marker
    return f'UNKNOWN:{type_str}'


def convert_command(cmd_data: dict) -> dict:
    """Convert a single command definition."""
    result = {}
    
    # Convert send args
    send_args = []
    for arg in cmd_data.get('args', []):
        send_args.append({
            'name': sanitize_name(arg['name']),
            'type': map_type(arg['type']),
            'original_name': arg['name'],  # Keep original for reference
        })
    
    # Convert response args
    recv_args = []
    for arg in cmd_data.get('resp', []):
        recv_args.append({
            'name': sanitize_name(arg['name']),
            'type': map_type(arg['type']),
            'original_name': arg['name'],
        })
    
    result['send'] = normalize_size_fields(send_args)
    result['recv'] = normalize_size_fields(recv_args)

    return result


def load_overrides(path: Path) -> dict:
    """
    Load hand-corrected command definitions that replace auto-generated ones.

    The overrides file is in final form ({name, type} entries). Each command
    found here fully replaces its auto-generated send/recv. ``original_name`` is
    backfilled from ``name`` when omitted.
    """
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    for cmd in data.values():
        for section in ('send', 'recv'):
            for arg in cmd.get(section) or []:
                arg.setdefault('original_name', arg['name'])
    return data


def convert_json_to_yaml(json_path: Path, yaml_path: Path,
                         overrides_path: Path = None) -> dict:
    """
    Convert the JSON configuration to YAML format.

    Returns statistics about the conversion.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    overrides = load_overrides(overrides_path) if overrides_path else {}

    yaml_data = {}
    stats = {
        'total_commands': 0,
        'unknown_types': set(),
        'commands_by_module': {},
        'size_fields_removed': 0,
        'commands_normalized': 0,
        'commands_overridden': 0,
    }

    for cmd_name, cmd_data in json_data.items():
        raw_fields = len(cmd_data.get('args', [])) + len(cmd_data.get('resp', []))
        converted = convert_command(cmd_data)
        kept_fields = len(converted['send']) + len(converted['recv'])
        removed = raw_fields - kept_fields
        if removed:
            stats['size_fields_removed'] += removed
            stats['commands_normalized'] += 1
        # Apply hand-corrected override (full replacement) if present.
        if cmd_name in overrides:
            converted = overrides[cmd_name]
            stats['commands_overridden'] += 1
        yaml_data[cmd_name] = converted
        stats['total_commands'] += 1

        # Track module (prefix before first dot)
        module = cmd_name.split('.')[0] if '.' in cmd_name else 'Other'
        stats['commands_by_module'][module] = stats['commands_by_module'].get(module, 0) + 1
        
        # Track unknown types
        for arg in converted['send'] + converted['recv']:
            if arg['type'].startswith('UNKNOWN:'):
                stats['unknown_types'].add(arg['type'])
    
    # Write YAML with custom formatting
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write("# Nanonis TCP Command Definitions\n")
        f.write("# Auto-generated from nanonis_tcp_auto.json\n")
        f.write("# Do not edit manually - regenerate using convert_json_to_yaml.py\n\n")
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return stats


def main():
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    json_path = project_root / 'configs' / 'nanonis_tcp_auto.json'
    yaml_path = project_root / 'configs' / 'nanonis_tcp.yaml'
    overrides_path = project_root / 'configs' / 'nanonis_tcp_overrides.yaml'

    # Ensure output directory exists
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Converting: {json_path}")
    print(f"Overrides: {overrides_path}")
    print(f"Output: {yaml_path}")

    stats = convert_json_to_yaml(json_path, yaml_path, overrides_path)
    
    print(f"\n=== Conversion Complete ===")
    print(f"Total commands: {stats['total_commands']}")
    print(f"Normalized (RC-2): removed {stats['size_fields_removed']} "
          f"redundant size field(s) across {stats['commands_normalized']} command(s)")
    print(f"Overridden (hand-corrected): {stats['commands_overridden']} command(s)")
    print(f"\nCommands by module:")
    for module, count in sorted(stats['commands_by_module'].items()):
        print(f"  {module}: {count}")
    
    if stats['unknown_types']:
        print(f"\n⚠️  Unknown types found:")
        for t in sorted(stats['unknown_types']):
            print(f"  {t}")
    else:
        print(f"\n✓ All types mapped successfully")


if __name__ == '__main__':
    main()
