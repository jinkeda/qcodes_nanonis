#!/usr/bin/env python3
"""
Split nanonis_tcp_auto.json into per-prefix JSON files.

Every command is grouped by its prefix - the part of the command name before
the first dot - and written to ``<prefix>.json`` in the output folder. The
per-command payload (``args``/``resp``) is copied verbatim, so the split files
together are equivalent to the source.

Examples
--------
    BiasSpectr.Open  -> BiasSpectr.json
    BiasSpectr.Stop  -> BiasSpectr.json
    BiasSwp.LimitsGet -> BiasSwp.json

Usage
-----
    python scripts/split_commands.py
    python scripts/split_commands.py --source configs/nanonis_tcp_auto.json \
                                     --out-dir configs/commands
    python scripts/split_commands.py --clean   # remove stale *.json first
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple


def command_prefix(command_name: str) -> str:
    """
    Return the prefix of a command name (the text before the first dot).

    Commands without a dot use the whole name as their prefix.
    """
    return command_name.split('.', 1)[0]


def group_by_prefix(commands: Dict[str, dict]) -> "OrderedDict[str, OrderedDict]":
    """
    Group commands by prefix, preserving the source ordering.

    Args:
        commands: Mapping of command name -> command payload.

    Returns:
        Mapping of prefix -> ordered mapping of command name -> payload.
    """
    groups: "OrderedDict[str, OrderedDict[str, dict]]" = OrderedDict()
    for name, payload in commands.items():
        prefix = command_prefix(name)
        groups.setdefault(prefix, OrderedDict())[name] = payload
    return groups


def write_groups(
    groups: "OrderedDict[str, OrderedDict]",
    out_dir: Path,
) -> List[Tuple[Path, int]]:
    """
    Write each prefix group to ``<out_dir>/<prefix>.json``.

    Returns:
        List of (path, command_count) for each file written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Tuple[Path, int]] = []
    for prefix, group in groups.items():
        path = out_dir / f"{prefix}.json"
        with path.open('w', encoding='utf-8') as f:
            json.dump(group, f, indent=4, ensure_ascii=False)
            f.write('\n')
        written.append((path, len(group)))
    return written


def clean_dir(out_dir: Path) -> int:
    """Remove existing ``*.json`` files from the output folder. Returns count."""
    if not out_dir.exists():
        return 0
    removed = 0
    for path in out_dir.glob('*.json'):
        path.unlink()
        removed += 1
    return removed


def parse_args(argv) -> argparse.Namespace:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--source',
        type=Path,
        default=project_root / 'configs' / 'nanonis_tcp_auto.json',
        help='Source JSON with all command definitions '
             '(default: configs/nanonis_tcp_auto.json)',
    )
    parser.add_argument(
        '--out-dir',
        type=Path,
        default=project_root / 'configs' / 'commands',
        help='Folder to write the per-prefix JSON files into '
             '(default: configs/commands)',
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Remove existing *.json files in the output folder before writing',
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not args.source.exists():
        print(f"Error: source file not found: {args.source}", file=sys.stderr)
        return 1

    with args.source.open('r', encoding='utf-8') as f:
        commands = json.load(f, object_pairs_hook=OrderedDict)

    groups = group_by_prefix(commands)

    if args.clean:
        removed = clean_dir(args.out_dir)
        if removed:
            print(f"Removed {removed} existing JSON file(s) from {args.out_dir}")

    written = write_groups(groups, args.out_dir)

    total_cmds = sum(count for _, count in written)
    print(f"Source:  {args.source} ({len(commands)} commands)")
    print(f"Output:  {args.out_dir}")
    print(f"Wrote {len(written)} file(s), {total_cmds} commands total:\n")
    for path, count in sorted(written, key=lambda x: x[0].name.lower()):
        print(f"  {path.name:<24} {count:>3} command(s)")

    if total_cmds != len(commands):
        print(
            f"\nWarning: command count mismatch "
            f"(source={len(commands)}, written={total_cmds})",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
