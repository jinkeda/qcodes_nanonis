#!/usr/bin/env python3
"""
Extract command definitions from nanonis_tramea package.

This script parses the NanonisClass.py file to extract all methods
and their type signatures, then converts them to YAML format.
"""

import re
import ast
from pathlib import Path
import yaml


# Type mapping from tramea DSL to our format
TYPE_MAPPING = {
    'H': 'uint16',
    'h': 'int16',
    'I': 'uint32',
    'i': 'int32',
    'f': 'float32',
    'd': 'float64',
    # Array types
    '+*i': 'array_int32',
    '*i': 'array_int32',
    '-*i': 'array_int32',
    '**i': 'array_int32',
    '+*I': 'array_uint32',
    '*I': 'array_uint32',
    '-*I': 'array_uint32',
    '**I': 'array_uint32',
    '+*f': 'array_float32',
    '*f': 'array_float32',
    '-*f': 'array_float32',
    '**f': 'array_float32',
    '+*d': 'array_float64',
    '*d': 'array_float64',
    '-*d': 'array_float64',
    '**d': 'array_float64',
    '+*c': 'string',
    '*-c': 'string',
    '-*c': 'string',
    '*+c': 'array_string',
    '**c': 'array_string',
    '2f': 'matrix_float32',
    '2d': 'matrix_float64',
    '+2f': 'matrix_float32',
    '-2f': 'matrix_float32',
}


def sanitize_name(name: str) -> str:
    """Convert parameter name to Python identifier."""
    name = name.replace(' ', '_')
    name = name.replace('-', '_')
    name = name.replace('/', '_')
    name = name.replace('(', '_')
    name = name.replace(')', '')
    name = re.sub(r'_+', '_', name)
    name = name.strip('_').lower()
    return name or 'unnamed'


def map_type(type_code: str) -> str:
    """Map tramea type code to our type string."""
    if type_code in TYPE_MAPPING:
        return TYPE_MAPPING[type_code]
    
    # Handle special cases
    type_code_lower = type_code.lower()
    for key, value in TYPE_MAPPING.items():
        if type_code_lower == key.lower():
            return value
    
    # Return as-is for unknown types
    return f'UNKNOWN:{type_code}'


def extract_quicksend_call(method_body: str) -> dict:
    """Extract quickSend parameters from method body."""
    # Pattern to match quickSend call
    pattern = r'self\.quickSend\s*\(\s*["\']([^"\']+)["\']\s*,\s*\[([^\]]*)\]\s*,\s*\[([^\]]*)\]\s*,\s*\[([^\]]*)\]\s*\)'
    match = re.search(pattern, method_body, re.DOTALL)
    
    if not match:
        return None
    
    command_name = match.group(1)
    body_args = match.group(2).strip()
    body_types = match.group(3).strip()
    response_types = match.group(4).strip()
    
    return {
        'command': command_name,
        'body_args': body_args,
        'body_types': body_types,
        'response_types': response_types,
    }


def parse_type_list(types_str: str) -> list:
    """Parse a comma-separated list of type codes."""
    if not types_str.strip():
        return []
    
    # Remove quotes and split
    types_str = types_str.replace('"', '').replace("'", "")
    types = [t.strip() for t in types_str.split(',')]
    return [t for t in types if t]


def extract_param_names(method_def: str) -> list:
    """Extract parameter names from method definition."""
    # Match def method_name(self, param1, param2, ...)
    pattern = r'def\s+\w+\s*\(\s*self\s*(?:,\s*([^)]+))?\s*\)'
    match = re.search(pattern, method_def)
    
    if not match or not match.group(1):
        return []
    
    params_str = match.group(1)
    params = []
    for p in params_str.split(','):
        p = p.strip()
        # Remove type hints and default values
        p = re.sub(r':.*', '', p)
        p = re.sub(r'=.*', '', p)
        p = p.strip()
        if p:
            params.append(p)
    
    return params


def parse_nanonis_class(file_path: Path) -> dict:
    """Parse NanonisClass.py and extract all command definitions."""
    content = file_path.read_text(encoding='utf-8')
    
    commands = {}
    
    # Find all method definitions that use quickSend
    method_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:.*?return\s+self\.quickSend\s*\([^)]+\)'
    
    for match in re.finditer(method_pattern, content, re.DOTALL):
        method_text = match.group(0)
        method_name = match.group(1)
        
        # Skip internal methods
        if method_name.startswith('_') or method_name in ['send', 'quickSend', 'close', 
                                                           'returnDebugInfo', 'printDebugInfo',
                                                           'handleString', 'handleArray',
                                                           'handleArrayPrepend', 'handleArrayString',
                                                           'handle2DArray', 'correctType',
                                                           'decodeArray', 'decodeStringPrepended',
                                                           'decodeSingularString', 'decodeArrayPrepended',
                                                           'parseError', 'parseGeneralResponse']:
            continue
        
        # Extract quickSend call details
        qs_info = extract_quicksend_call(method_text)
        if not qs_info:
            continue
        
        command_name = qs_info['command']
        
        # Parse types
        send_types = parse_type_list(qs_info['body_types'])
        recv_types = parse_type_list(qs_info['response_types'])
        
        # Get parameter names
        param_names = extract_param_names(method_text)
        
        # Build send args
        send_args = []
        for i, type_code in enumerate(send_types):
            name = param_names[i] if i < len(param_names) else f'arg{i}'
            send_args.append({
                'name': sanitize_name(name),
                'type': map_type(type_code),
                'original_name': name,
            })
        
        # Build recv args
        recv_args = []
        for i, type_code in enumerate(recv_types):
            recv_args.append({
                'name': f'return_{i}',
                'type': map_type(type_code),
            })
        
        commands[command_name] = {
            'send': send_args,
            'recv': recv_args,
        }
    
    return commands


def main():
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    tramea_path = project_root.parent / 'reference' / 'nanonis_tramea-1.0.7' / 'nanonis_tramea' / 'NanonisClass.py'
    output_path = project_root / 'configs' / 'nanonis_tramea.yaml'
    
    print(f"Parsing: {tramea_path}")
    
    if not tramea_path.exists():
        print(f"Error: {tramea_path} not found")
        return
    
    commands = parse_nanonis_class(tramea_path)
    
    # Write YAML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Nanonis TRAMEA Command Definitions\n")
        f.write("# Extracted from nanonis_tramea-1.0.7\n")
        f.write(f"# Total commands: {len(commands)}\n\n")
        yaml.dump(commands, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\n=== Extraction Complete ===")
    print(f"Total commands: {len(commands)}")
    print(f"Output: {output_path}")
    
    # Show modules
    modules = {}
    for cmd in commands:
        module = cmd.split('.')[0] if '.' in cmd else 'Other'
        modules[module] = modules.get(module, 0) + 1
    
    print(f"\nCommands by module:")
    for module, count in sorted(modules.items()):
        print(f"  {module}: {count}")


if __name__ == '__main__':
    main()
