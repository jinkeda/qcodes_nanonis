import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

import PyPDF2

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)

TYPE_ALIASES: Dict[str, str] = {
    "float32": "f",
    "float 32": "f",
    "float64": "d",
    "float 64": "d",
    "int32": "i",
    "int 32": "i",
    "int": "i",
    "unsigned int32": "I",
    "unsigned int 32": "I",
    "uint32": "I",
    "unsigned int16": "H",
    "unsigned int 16": "H",
    "uint16": "H",
    "string": "s",
    "1d array string": "1D array string",
    "1 d array string": "1D array string",
    "1d array float32": "1D array float32",
    "1 d array float32": "1D array float32",
    "1d array float 32": "1D array float32",
    "1d array int": "1D array int",
    "1 d array int": "1D array int",
    "2d array string": "2D array string",
    "2 d array string": "2D array string",
    "2d array float32": "2D array float32",
    "2 d array float32": "2D array float32",
    "1d array float64": "1D array float64",
    "1 d array float64": "1D array float64",
}

CHOICE_PATTERN = re.compile(r"^\d+\s*=", re.IGNORECASE)
COMMAND_PATTERN = re.compile(r"^[A-Za-z][\w]*(?:\.[A-Za-z0-9_]+)+$")
NAME_TRIM_PATTERN = re.compile(r"\s+is\s+", re.IGNORECASE)

USAGE = (
    "Usage: python generate_nanonis_tcp.py <pdf> <output> "
    "[--start-page <int>] [--existing <path>]"
)


class HelpRequested(Exception):
    """Raised when the user requests help."""


class UsageError(Exception):
    """Raised when CLI arguments are invalid."""


def normalize_type(type_text: str) -> Optional[str]:
    raw = re.sub(r"\s+", " ", type_text.strip()).lower()
    if not raw:
        return None
    if raw in TYPE_ALIASES:
        return TYPE_ALIASES[raw]

    if raw.startswith("1d array") or raw.startswith("2d array"):
        raw = raw.replace("1d", "1D").replace("2d", "2D")
        raw = raw.replace("  ", " ")
        return raw

    LOGGER.warning("Unmapped data type '%s'", type_text)
    return None


def clean_name(raw: str) -> str:
    if not raw:
        return ""
    name = " ".join(raw.split())
    return NAME_TRIM_PATTERN.split(name, 1)[0].strip()


def _entry(name: str, type_code: Optional[str]) -> Optional[Dict[str, str]]:
    clean = clean_name(name)
    if not clean or not type_code:
        return None
    return {"name": clean, "type": type_code}


def sanitize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {"args": [], "resp": []}

    arg_types = payload.get("argTypes") if isinstance(payload.get("argTypes"), Mapping) else {}
    args_source = payload.get("args", [])
    seen_args = set()

    if isinstance(args_source, list):
        for item in args_source:
            if isinstance(item, Mapping):
                entry = _entry(item.get("name", ""), item.get("type"))
            elif isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
                entry = _entry(item[0], item[1])
            else:
                type_code = None
                if isinstance(arg_types, Mapping):
                    type_code = arg_types.get(item) or arg_types.get(clean_name(item))
                entry = _entry(item, type_code)
            if entry and entry["name"] not in seen_args:
                sanitized["args"].append(entry)
                seen_args.add(entry["name"])

    if isinstance(arg_types, Mapping):
        for name, type_code in arg_types.items():
            entry = _entry(name, type_code)
            if entry and entry["name"] not in seen_args:
                sanitized["args"].append(entry)
                seen_args.add(entry["name"])

    resp_source = payload.get("respTypes") or payload.get("resp") or []
    seen_resp = set()

    if isinstance(resp_source, Mapping):
        items = resp_source.items()
    elif isinstance(resp_source, list):
        items = []
        for item in resp_source:
            if isinstance(item, Mapping):
                items.append((item.get("name", ""), item.get("type")))
            elif isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
                items.append((item[0], item[1]))
    else:
        items = []

    for name, type_code in items:
        entry = _entry(name, type_code)
        if entry and entry["name"] not in seen_resp:
            sanitized["resp"].append(entry)
            seen_resp.add(entry["name"])

    return sanitized


def parse_bullet(line: str) -> Optional[Tuple[str, str]]:
    content = line.lstrip("- ")
    if not content or content.lower().startswith("none"):
        return None
    if CHOICE_PATTERN.match(content.replace(" ", "")):
        return None

    lowered = content.lower()
    type_match: Optional[Tuple[int, int, str]] = None
    for alias in sorted(TYPE_ALIASES, key=len, reverse=True):
        idx = lowered.find(alias)
        if idx >= 0:
            type_match = (idx, idx + len(alias), TYPE_ALIASES[alias])
            break

    if type_match is None:
        array_match = re.search(r"(\d+d array [^()]+)", lowered)
        if array_match:
            type_code = normalize_type(array_match.group(1))
            idx = array_match.start(1)
            type_match = (idx, array_match.end(1), type_code)

    if type_match is None:
        LOGGER.debug("Could not determine type from line: %s", content)
        return None

    start, _, type_code = type_match
    if type_code is None:
        return None

    name_part = content[:start].rstrip(" -:\t")
    if name_part.endswith("("):
        name_part = name_part[:-1].rstrip()
    name = clean_name(name_part if name_part else "arg")
    return name, type_code


def parse_pdf(pdf_path: Path, start_page: int = 0) -> Dict[str, Dict[str, Any]]:
    reader = PyPDF2.PdfReader(str(pdf_path))
    commands: Dict[str, Dict[str, Any]] = {}

    current_cmd: Optional[str] = None
    state: Optional[str] = None

    for page_index in range(start_page, len(reader.pages)):
        page_text = reader.pages[page_index].extract_text() or ""
        for raw_line in page_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("Page "):
                continue

            if COMMAND_PATTERN.match(line):
                current_cmd = line
                commands.setdefault(current_cmd, {"args": [], "resp": []})
                state = None
                continue

            lower = line.lower()
            if lower.startswith("arguments:"):
                state = None if "none" in lower else "args"
                continue
            if lower.startswith("return arguments"):
                state = None if "none" in lower else "resp"
                continue

            if current_cmd is None or state is None or not line.startswith("-"):
                continue

            parsed = parse_bullet(line)
            if not parsed:
                continue
            name, type_code = parsed
            record = commands[current_cmd]

            if state == "args":
                entry = _entry(name, type_code)
                if entry:
                    record["args"].append(entry)
            else:
                if "error" in name.lower():
                    continue
                entry = _entry(name, type_code)
                if entry:
                    record["resp"].append(entry)

    return commands


def merge_with_existing(new_data: Mapping[str, Dict[str, Any]], existing: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    sanitized_existing = {
        name: sanitize_payload(payload)
        for name, payload in existing.items()
        if isinstance(payload, MutableMapping)
    }

    merged: Dict[str, Dict[str, Any]] = {
        name: sanitize_payload(payload)
        for name, payload in new_data.items()
    }

    for name, payload in sanitized_existing.items():
        if name in merged:
            existing_args = {entry["name"]: entry for entry in merged[name]["args"]}
            for entry in payload["args"]:
                existing_args.setdefault(entry["name"], entry)
            merged[name]["args"] = list(existing_args.values())

            existing_resp = {entry["name"]: entry for entry in merged[name]["resp"]}
            for entry in payload["resp"]:
                existing_resp.setdefault(entry["name"], entry)
            merged[name]["resp"] = list(existing_resp.values())
        else:
            merged[name] = payload

    return merged


def parse_cli_args(argv: Sequence[str]) -> Tuple[Path, Path, int, Optional[Path]]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise HelpRequested
    if len(argv) < 2:
        raise UsageError("Missing required arguments.")

    pdf = Path(argv[0])
    output = Path(argv[1])
    start_page = 37
    existing: Optional[Path] = None

    index = 2
    while index < len(argv):
        arg = argv[index]
        if arg == "--start-page":
            index += 1
            if index >= len(argv):
                raise UsageError("Expected value after --start-page")
            try:
                start_page = int(argv[index])
            except ValueError as exc:
                raise UsageError("--start-page expects an integer") from exc
        elif arg.startswith("--start-page="):
            try:
                start_page = int(arg.split("=", 1)[1])
            except ValueError as exc:
                raise UsageError("--start-page expects an integer") from exc
        elif arg == "--existing":
            index += 1
            if index >= len(argv):
                raise UsageError("Expected value after --existing")
            existing = Path(argv[index])
        elif arg.startswith("--existing="):
            existing = Path(arg.split("=", 1)[1])
        else:
            raise UsageError(f"Unknown argument: {arg}")
        index += 1

    return pdf, output, start_page, existing


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    try:
        pdf_path, output_path, start_page, existing_path = parse_cli_args(argv)
    except HelpRequested:
        print(USAGE)
        return 0
    except UsageError as exc:
        LOGGER.error(str(exc))
        print(USAGE, file=sys.stderr)
        return 1

    LOGGER.info("Parsing commands from %s starting at page %s", pdf_path, start_page)
    commands = parse_pdf(pdf_path, start_page=start_page)
    commands = {cmd: sanitize_payload(payload) for cmd, payload in commands.items()}

    if existing_path and existing_path.exists():
        LOGGER.info("Merging definitions from existing JSON: %s", existing_path)
        existing_data = json.loads(existing_path.read_text(encoding="utf-8"))
        commands = merge_with_existing(commands, existing_data)

    output_path.write_text(json.dumps(commands, indent=4, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Wrote output to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
