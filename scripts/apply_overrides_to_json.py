#!/usr/bin/env python3
"""
Apply the hand-corrected definitions in nanonis_tcp_overrides.yaml back into the
JSON source (nanonis_tcp_auto.json), so the JSON and the generated YAML stay
consistent.

The overrides file is the single editable source of truth for corrections
(written in readable types like ``float32`` / ``array_string``). This script
converts those entries to the JSON short-code format (``f`` / ``1D array
string`` ...) and replaces the corresponding commands in the JSON.

Usage
-----
    python scripts/apply_overrides_to_json.py
    python scripts/apply_overrides_to_json.py --no-split   # skip re-splitting
"""

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Readable type -> JSON short code (inverse of convert_json_to_yaml.TYPE_MAPPING).
READABLE_TO_CODE = {
    'float32': 'f',
    'float64': 'd',
    'int32': 'i',
    'uint32': 'I',
    'uint16': 'H',
    'int16': 'h',
    'string': 's',
    'array_float32': '1D array float32',
    'array_float64': '1D array float64',
    'array_int32': '1D array int',
    'array_string': '1D array string',
    'matrix_float32': '2D array float32',
    'matrix_string': '2D array string',
}


def to_json_args(entries) -> list:
    """Convert override {name,type} entries to JSON {name,type} with short codes."""
    out = []
    for arg in entries or []:
        rtype = arg['type']
        if rtype not in READABLE_TO_CODE:
            raise ValueError(f"No JSON short code for type '{rtype}'")
        name = arg.get('original_name') or arg['name']
        out.append({'name': name, 'type': READABLE_TO_CODE[rtype]})
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--json', type=Path,
                        default=PROJECT_ROOT / 'configs' / 'nanonis_tcp_auto.json')
    parser.add_argument('--overrides', type=Path,
                        default=PROJECT_ROOT / 'configs' / 'nanonis_tcp_overrides.yaml')
    parser.add_argument('--no-split', action='store_true',
                        help="Don't re-run split_commands.py afterwards")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    with args.json.open('r', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    with args.overrides.open('r', encoding='utf-8') as f:
        overrides = yaml.safe_load(f) or {}

    applied, added = [], []
    for cmd, defn in overrides.items():
        entry = OrderedDict(
            args=to_json_args(defn.get('send')),
            resp=to_json_args(defn.get('recv')),
        )
        if cmd in data:
            applied.append(cmd)
        else:
            added.append(cmd)
        data[cmd] = entry

    with args.json.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')

    print(f"Applied {len(applied)} override(s) into {args.json.name}"
          + (f", added {len(added)} new" if added else ""))
    for c in applied + added:
        print(f"  {c}")

    if not args.no_split:
        print("\nRe-splitting per-prefix JSON files...")
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'scripts' / 'split_commands.py'), '--clean'],
            check=True,
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
