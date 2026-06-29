#!/usr/bin/env python3
"""
Live test of every Nanonis TCP command defined in a YAML config.

For each command this script:
  1. Synthesizes neutral arguments (0 / 0.0 / '' / empty array) from the
     command's ``send`` definition.
  2. Sends the command over TCP and reads the full response.
  3. Decodes the response against the ``recv`` definition and checks:
       - all expected components decode,
       - no trailing/short bytes (structure matches the definition),
       - the Nanonis error status is 0 and the error string is empty.

It then classifies each command and writes a structured Markdown report.

WARNING: this sends *every* command, including state-changing ones. Only run
it against a Nanonis simulator or a rig where neutral writes are harmless.

Usage
-----
    python scripts/live_test_commands.py
    python scripts/live_test_commands.py --host 127.0.0.1 --port 6501 \
        --config configs/commands --report live_test_report.md
"""

import argparse
import struct
import sys
import traceback
from pathlib import Path
from typing import Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from nanonis.command import NanonisController  # noqa: E402
from nanonis.protocol.exceptions import (  # noqa: E402
    NanonisConnectionError,
    NanonisTimeoutError,
)

# Commands that must never be sent: they terminate or destabilize the server
# itself, which would abort the rest of the run.
DEFAULT_SKIP = {
    'Util.Quit',  # tells the Nanonis software to quit -> kills the connection
}

# Result categories
SKIPPED = 'SKIPPED'
PASS = 'PASS'
MODULE_UNAVAILABLE = 'MODULE_UNAVAILABLE'  # module/feature/scanner not present (env, not a bug)
PROTOCOL_MISMATCH = 'PROTOCOL_MISMATCH'    # Nanonis could not unflatten request -> wrong send types
NANONIS_ERROR = 'NANONIS_ERROR'        # other non-zero Nanonis error status
DECODE_ERROR = 'DECODE_ERROR'          # response could not be decoded per definition
STRUCTURE_MISMATCH = 'STRUCTURE_MISMATCH'  # decoded, but byte count != definition
ENCODE_ERROR = 'ENCODE_ERROR'          # could not even build the request
CONNECTION_ERROR = 'CONNECTION_ERROR'  # socket/timeout failure

# Substrings that mark an error as an environment limitation rather than a bug
_MODULE_MARKERS = (
    'not available', 'make sure', 'module is running', 'cannot access',
    'could not access', 'incorrect scanner index',
)


def order_commands_for_live_test(commands: List[str]) -> List[str]:
    """Run module-opening commands before commands that depend on them."""
    return sorted(commands, key=lambda name: (not name.endswith('.Open'), name))


def classify_nanonis_error(message: str) -> str:
    """Sub-classify a non-zero Nanonis error message into a category."""
    msg = message.lower()
    if any(marker in msg for marker in _MODULE_MARKERS):
        return MODULE_UNAVAILABLE
    if 'unflatten' in msg:
        return PROTOCOL_MISMATCH
    return NANONIS_ERROR


def synth_arg(dtype: str) -> Any:
    """Return a neutral value for a send argument of the given type."""
    if dtype in ('float32', 'float64'):
        return 0.0
    if dtype in ('int16', 'int32', 'uint16', 'uint32', 'bool'):
        return 0
    if dtype == 'string':
        return ''
    if dtype.startswith('array_') or dtype.startswith('matrix_'):
        return []  # empty array; the preceding count field is synthesized as 0
    return 0


def parse_error_trailer(data: bytes) -> Tuple[int, str, int]:
    """
    Parse the Nanonis error trailer.

    Returns (error_status, error_description, trailer_size_in_bytes).
    """
    if len(data) < 8:
        return 0, '', len(data)
    status = struct.unpack('>I', data[:4])[0]
    length = struct.unpack('>i', data[4:8])[0]
    desc = ''
    if length > 0:
        desc = data[8:8 + length].decode('utf-8', errors='replace')
    return status, desc, 8 + max(length, 0)


def validate_response(decoder, recv_types: List[Tuple[str, str]], response: bytes):
    """
    Decode recv args and validate structure + error trailer.

    Returns a dict with keys: category, detail, decoded, leftover, error_status.
    Raises nothing - decode failures are reported in the category.
    """
    offset = 0
    decoded_ctx: List[Tuple[str, Any]] = []
    decoded: dict = {}
    try:
        for name, dtype in recv_types:
            value, consumed = decoder._decode_value(dtype, response[offset:], decoded_ctx)
            decoded[name] = value
            decoded_ctx.append((dtype, value))
            offset += consumed
    except Exception as exc:  # noqa: BLE001 - want the message for the report
        return {
            'category': DECODE_ERROR,
            'detail': f"{type(exc).__name__}: {exc}",
            'decoded': decoded,
            'leftover': None,
            'error_status': None,
        }

    status, desc, trailer_size = parse_error_trailer(response[offset:])
    leftover = len(response) - offset - trailer_size

    if status != 0 or desc:
        return {
            'category': classify_nanonis_error(desc),
            'detail': f"error status={status}, message={desc!r}",
            'decoded': decoded,
            'leftover': leftover,
            'error_status': status,
        }
    if leftover != 0:
        return {
            'category': STRUCTURE_MISMATCH,
            'detail': (
                f"decoded {offset} body byte(s) + {trailer_size} trailer byte(s), "
                f"but response is {len(response)} byte(s) "
                f"({leftover:+d} unaccounted)"
            ),
            'decoded': decoded,
            'leftover': leftover,
            'error_status': status,
        }
    return {
        'category': PASS,
        'detail': 'ok',
        'decoded': decoded,
        'leftover': 0,
        'error_status': 0,
    }


def test_command(ctrl: NanonisController, name: str) -> dict:
    """Run one command and return a result record."""
    cmd_def = ctrl._registry.get(name)
    send_types = cmd_def.get_send_types()
    recv_types = cmd_def.get_recv_types()
    args = tuple(synth_arg(t) for _, t in send_types)

    record = {
        'name': name,
        'n_send': len(send_types),
        'n_recv': len(recv_types),
        'args': args,
        'category': None,
        'detail': '',
    }

    # Encode request
    try:
        body = ctrl._encoder.encode(send_types, args)
    except Exception as exc:  # noqa: BLE001
        record['category'] = ENCODE_ERROR
        record['detail'] = f"{type(exc).__name__}: {exc}"
        return record

    # Send + receive (full body, including error trailer)
    try:
        response = ctrl._client.send_raw(name, body)
    except (NanonisConnectionError, NanonisTimeoutError) as exc:
        record['category'] = CONNECTION_ERROR
        record['detail'] = f"{type(exc).__name__}: {exc}"
        record['_needs_reconnect'] = True
        return record
    except Exception as exc:  # noqa: BLE001
        record['category'] = CONNECTION_ERROR
        record['detail'] = f"{type(exc).__name__}: {exc}"
        record['_needs_reconnect'] = True
        return record

    result = validate_response(ctrl._decoder, recv_types, response)
    record['category'] = result['category']
    record['detail'] = result['detail']
    record['resp_len'] = len(response)
    return record


def likely_reason(record: dict) -> str:
    """Heuristic explanation for a failure category."""
    cat = record['category']
    if cat == MODULE_UNAVAILABLE:
        return ("The relevant module/feature/scanner is not running in this "
                "session (environment limitation). The command definition is "
                "probably fine - retest with that module enabled.")
    if cat == PROTOCOL_MISMATCH:
        return ("Nanonis could not unflatten the request body -> the command's "
                "SEND argument types/order/count in the YAML do not match the "
                "real protocol. Fix the send definition.")
    if cat == NANONIS_ERROR:
        return ("Nanonis rejected the request - usually the synthesized neutral "
                "argument is out of range/invalid for this command, or the command "
                "is not available in this controller/mode.")
    if cat == DECODE_ERROR:
        return ("Response could not be parsed against the recv definition - the "
                "command's recv types in the YAML likely don't match the real "
                "response (wrong/missing types or array-size field).")
    if cat == STRUCTURE_MISMATCH:
        return ("Response decoded but byte count differs from the definition - the "
                "recv definition has too many/few fields or a wrong type.")
    if cat == ENCODE_ERROR:
        return "Send definition has a type the encoder doesn't support."
    if cat == CONNECTION_ERROR:
        return ("No/short response - command may block (wait-until-done), be "
                "unsupported, or have crashed the connection.")
    return ''


def build_report(records: List[dict], host: str, port: int, config: Path) -> str:
    by_cat: dict = {}
    for r in records:
        by_cat.setdefault(r['category'], []).append(r)

    total = len(records)
    skipped = len(by_cat.get(SKIPPED, []))
    tested = total - skipped
    passed = len(by_cat.get(PASS, []))
    failed = tested - passed

    lines: List[str] = []
    lines.append("# Nanonis Live Command Test Report")
    lines.append("")
    lines.append(f"- Target: `{host}:{port}`")
    lines.append(f"- Config: `{config}`")
    lines.append(f"- Total commands in config: **{total}**")
    lines.append(f"- Skipped (destructive): **{skipped}**")
    lines.append(f"- Tested: **{tested}**")
    lines.append(f"- Successful: **{passed}**")
    lines.append(f"- Failed: **{failed}**")
    lines.append("")
    lines.append("## Breakdown by category")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat in (PASS, MODULE_UNAVAILABLE, PROTOCOL_MISMATCH, NANONIS_ERROR,
                STRUCTURE_MISMATCH, DECODE_ERROR, ENCODE_ERROR,
                CONNECTION_ERROR, SKIPPED):
        lines.append(f"| {cat} | {len(by_cat.get(cat, []))} |")
    lines.append("")

    # Definition bugs = failures attributable to the command definition itself
    # (as opposed to environment limitations like a missing module).
    bug_cats = (PROTOCOL_MISMATCH, DECODE_ERROR, STRUCTURE_MISMATCH, ENCODE_ERROR)
    bugs = [r for r in records if r['category'] in bug_cats]
    bug_names = ', '.join(f"`{record['name']}`" for record in bugs) if bugs else 'none'
    lines.append(f"**Likely command-definition bugs (actionable): {len(bugs)}** "
                 f"— {bug_names}")
    lines.append("")

    if failed == 0:
        lines.append("All commands passed. ✅")
    else:
        lines.append("## Failed commands")
        lines.append("")
        lines.append("| Command | Category | Detail |")
        lines.append("|---------|----------|--------|")
        for r in records:
            if r['category'] in (PASS, SKIPPED):
                continue
            detail = r['detail'].replace('|', '\\|')
            lines.append(f"| `{r['name']}` | {r['category']} | {detail} |")
        lines.append("")
        lines.append("## Per-failure analysis")
        lines.append("")
        for r in records:
            if r['category'] in (PASS, SKIPPED):
                continue
            lines.append(f"### `{r['name']}`  ({r['category']})")
            lines.append(f"- send args: {r['n_send']}, recv args: {r['n_recv']}")
            lines.append(f"- sent values: `{r['args']}`")
            lines.append(f"- detail: {r['detail']}")
            lines.append(f"- likely reason: {likely_reason(r)}")
            lines.append("")

    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=6501)
    parser.add_argument('--config', type=Path,
                        default=PROJECT_ROOT / 'configs' / 'commands')
    parser.add_argument('--report', type=Path,
                        default=PROJECT_ROOT / 'live_test_report.md')
    parser.add_argument('--timeout', type=float, default=5.0)
    parser.add_argument('--skip', nargs='*', default=None,
                        help='Command names to skip (default: destructive meta-commands)')
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    skip = set(args.skip) if args.skip is not None else set(DEFAULT_SKIP)

    ctrl = NanonisController(args.host, args.port, args.config, timeout=args.timeout)
    ctrl.connect()
    commands = order_commands_for_live_test(ctrl.list_commands())
    print(f"Testing {len(commands)} commands against {args.host}:{args.port} "
          f"(skipping {len(skip & set(commands))}) ...\n")

    records: List[dict] = []
    for i, name in enumerate(commands, 1):
        if name in skip:
            rec = {'name': name, 'n_send': 0, 'n_recv': 0, 'args': (),
                   'category': SKIPPED, 'detail': 'destructive - not sent'}
            records.append(rec)
            print(f"[{i:3}/{len(commands)}] skip {name:<32} {SKIPPED}")
            continue
        try:
            rec = test_command(ctrl, name)
        except Exception as exc:  # noqa: BLE001 - never let one command kill the run
            rec = {'name': name, 'n_send': 0, 'n_recv': 0, 'args': (),
                   'category': DECODE_ERROR,
                   'detail': f"harness error: {type(exc).__name__}: {exc}"}
            traceback.print_exc()
        records.append(rec)
        flag = 'ok ' if rec['category'] == PASS else 'FAIL'
        print(f"[{i:3}/{len(commands)}] {flag} {name:<32} {rec['category']}")
        # Reconnect if the socket may be desynced
        if rec.get('_needs_reconnect'):
            try:
                ctrl.disconnect()
                ctrl.connect()
            except Exception:  # noqa: BLE001
                print("  ! reconnect failed; aborting")
                break

    ctrl.disconnect()

    report = build_report(records, args.host, args.port, args.config)
    args.report.write_text(report, encoding='utf-8')

    passed = sum(1 for r in records if r['category'] == PASS)
    print(f"\n=== {passed}/{len(records)} passed; "
          f"{len(records) - passed} failed ===")
    print(f"Report written to {args.report}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
