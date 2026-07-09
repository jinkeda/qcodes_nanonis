import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

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
    "1d array unsigned int32": "1D array unsigned int32",
    "1 d array unsigned int32": "1D array unsigned int32",
    "1d array unsigned int8": "1D array unsigned int8",
    "1 d array unsigned int8": "1D array unsigned int8",
}

CHOICE_PATTERN = re.compile(r"^\d+\s*=", re.IGNORECASE)
COMMAND_PATTERN = re.compile(r"^[A-Za-z][\w]*(?:\.[A-Za-z0-9_]+)+$")
NAME_TRIM_PATTERN = re.compile(r"\s+is\s+", re.IGNORECASE)

USAGE = (
    "Usage: python generate_nanonis_tcp.py <pdf> <output-directory> "
    "[--start-page <int>] [--existing <command-directory>] [--module <name>]"
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
            if entry:
                sanitized["args"].append(entry)

    if isinstance(arg_types, Mapping):
        for name, type_code in arg_types.items():
            entry = _entry(name, type_code)
            if entry:
                sanitized["args"].append(entry)

    resp_source = payload.get("respTypes") or payload.get("resp") or []
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
        if entry:
            sanitized["resp"].append(entry)

    return sanitized


def parse_bullet(line: str) -> Optional[Tuple[str, str]]:
    content = line.lstrip("- ")
    if not content or content.lower().startswith("none"):
        return None
    if CHOICE_PATTERN.match(content.replace(" ", "")):
        return None

    aliases = "|".join(
        re.escape(alias) for alias in sorted(TYPE_ALIASES, key=len, reverse=True)
    )
    # Require the type to begin immediately after an opening parenthesis. This
    # avoids matching short aliases such as ``int`` inside ordinary prose. The
    # ``is`` alternative accepts two known missing-closing-parenthesis typos in
    # R14718 (BiasSpectr.MLSVals{Set,Get}).
    match = re.search(
        rf"\(\s*(?P<type>{aliases})(?=\s*\)|\s+is\b)",
        content,
        flags=re.IGNORECASE,
    )
    if match is None:
        LOGGER.debug("Could not determine type from line: %s", content)
        return None
    type_code = normalize_type(match.group("type"))
    if not type_code:
        return None

    name_part = content[: match.start()].rstrip(" -:\t")
    name = clean_name(name_part if name_part else "arg")
    return name, type_code


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract layout-preserving text with Poppler.

    PyPDF2 inserts spaces inside command names (for example
    ``BiasSpectr .Start``), which caused the historical command-boundary bleed.
    Poppler preserves the headings used as hard block boundaries.
    """

    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext (Poppler) is required for generation") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"pdftotext failed: {detail}") from exc
    return completed.stdout.decode("utf-8", errors="replace").replace(
        "\r\n", "\n"
    ).replace("\r", "\n")


def _normalize_scalar_strings(entries: Sequence[Mapping[str, str]]) -> list[Dict[str, str]]:
    """Drop the manual's separate scalar-string length field.

    Numeric and string arrays retain their independent size/count fields.
    """

    result: list[Dict[str, str]] = []
    integer_types = {"i", "I", "H"}
    for raw in entries:
        entry = dict(raw)
        if entry["type"] == "s" and result and result[-1]["type"] in integer_types:
            previous = result[-1]["name"].lower()
            current = entry["name"].lower()
            if "size" in previous or previous == current:
                result.pop()
        result.append(entry)
    return result


def _uniquify_names(entries: Sequence[Mapping[str, str]]) -> list[Dict[str, str]]:
    """Keep repeated wire fields addressable in decoded dictionaries."""

    counts: Dict[str, int] = {}
    result: list[Dict[str, str]] = []
    for raw in entries:
        entry = dict(raw)
        base = entry["name"]
        counts[base] = counts.get(base, 0) + 1
        if counts[base] > 1:
            entry["name"] = f"{base} {counts[base]}"
        result.append(entry)
    return result


def _parse_fields(text: str) -> list[Dict[str, str]]:
    fields: list[Dict[str, str]] = []
    for line in text.splitlines():
        if not re.match(r"^\s*-\s+", line):
            continue
        parsed = parse_bullet(line)
        if not parsed:
            continue
        name, type_code = parsed
        if "error" in name.lower():
            continue
        entry = _entry(name, type_code)
        if entry:
            fields.append(entry)
    return _uniquify_names(_normalize_scalar_strings(fields))


def parse_pdf(pdf_path: Path, start_page: int = 0) -> Dict[str, Dict[str, Any]]:
    del start_page  # Retained for CLI compatibility; TOC boundaries are authoritative.
    text = _extract_pdf_text(pdf_path)
    try:
        toc_end = text.index("Page 25")
    except ValueError as exc:
        raise RuntimeError("Could not locate the end of the protocol table of contents") from exc

    command_pattern = re.compile(
        r"^[\t \f]*([A-Za-z][A-Za-z0-9]*\.[A-Za-z0-9][A-Za-z0-9]*)"
        r"\s*\.{2,}\s*\d+\s*$",
        re.MULTILINE,
    )
    command_names = list(dict.fromkeys(command_pattern.findall(text[:toc_end])))
    if not command_names:
        raise RuntimeError("No commands found in the protocol table of contents")

    positions: list[Tuple[int, str]] = []
    for command in command_names:
        heading = re.search(
            rf"(?m)^[\t \f]*{re.escape(command)}[\t ]*$", text[toc_end:]
        )
        if heading is None:
            raise RuntimeError(f"Command body not found: {command}")
        positions.append((toc_end + heading.start(), command))
    positions.sort()

    commands: Dict[str, Dict[str, Any]] = {}
    for index, (start, command) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        block = text[start:end]
        if "Arguments:" not in block:
            raise RuntimeError(f"Arguments section not found: {command}")
        before_return, separator, after_return = block.partition("Return arguments")
        arguments = before_return.split("Arguments:", 1)[1]
        commands[command] = {
            "args": _parse_fields(arguments),
            # R14718 accidentally omits the error-only return heading for
            # HSSwp.SaveOptionsSet; an absent heading therefore means no data.
            "resp": _parse_fields(after_return) if separator else [],
        }

    return commands


def _runtime_types(payload: Mapping[str, Any], side: str) -> list[str]:
    entries = payload.get(side, [])
    if not isinstance(entries, list):
        return []
    return [
        entry["type"]
        for entry in _normalize_scalar_strings(entries)
        if isinstance(entry, Mapping) and "type" in entry
    ]


def merge_with_existing(new_data: Mapping[str, Dict[str, Any]], existing: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Preserve curated definitions only when their wire shape matches the PDF.

    The historical union-by-field-name merge caused adjacent-command fields to
    accumulate indefinitely. A shape mismatch now replaces the entire command
    with the freshly parsed manual definition.
    """

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
        if name not in merged:
            LOGGER.warning("Ignoring existing command absent from the manual: %s", name)
            continue
        generated = merged[name]
        if (
            _runtime_types(payload, "args") == _runtime_types(generated, "args")
            and _runtime_types(payload, "resp") == _runtime_types(generated, "resp")
        ):
            merged[name] = payload
        else:
            LOGGER.info("Replacing schema that differs from the manual: %s", name)

    return merged


def load_command_directory(path: Path) -> Dict[str, Any]:
    commands: Dict[str, Any] = {}
    for command_file in sorted(path.glob("*.json")):
        commands.update(json.loads(command_file.read_text(encoding="utf-8")))
    return commands


def write_command_directory(commands: Mapping[str, Any], path: Path) -> None:
    modules: Dict[str, Dict[str, Any]] = {}
    for command_name, payload in commands.items():
        module = command_name.split(".", 1)[0]
        modules.setdefault(module, {})[command_name] = payload

    path.mkdir(parents=True, exist_ok=True)
    for module, module_commands in sorted(modules.items()):
        output_file = path / f"{module}.json"
        output_file.write_text(
            json.dumps(module_commands, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def parse_cli_args(
    argv: Sequence[str],
) -> Tuple[Path, Path, int, Optional[Path], Optional[str]]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise HelpRequested
    if len(argv) < 2:
        raise UsageError("Missing required arguments.")

    pdf = Path(argv[0])
    output = Path(argv[1])
    start_page = 37
    existing: Optional[Path] = None
    module: Optional[str] = None

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
        elif arg == "--module":
            index += 1
            if index >= len(argv):
                raise UsageError("Expected value after --module")
            module = argv[index]
        elif arg.startswith("--module="):
            module = arg.split("=", 1)[1]
        else:
            raise UsageError(f"Unknown argument: {arg}")
        index += 1

    return pdf, output, start_page, existing, module


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    try:
        pdf_path, output_path, start_page, existing_path, module = parse_cli_args(argv)
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

    if existing_path and existing_path.is_dir():
        LOGGER.info("Merging definitions from command directory: %s", existing_path)
        existing_data = load_command_directory(existing_path)
        commands = merge_with_existing(commands, existing_data)

    if module:
        commands = {
            name: payload
            for name, payload in commands.items()
            if name.split(".", 1)[0] == module
        }
        if not commands:
            LOGGER.error("Module not found in the manual: %s", module)
            return 1

    write_command_directory(commands, output_path)
    LOGGER.info("Wrote %s commands to %s", len(commands), output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
