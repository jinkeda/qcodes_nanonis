# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 17:36:23 2023
Modified on April 3 2024
Modified on April 26 2025
author: k.jin  <k.jin@fz-juelich.de>
"""
import ast
import json
import logging
import os
import re
import struct
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
from qcodes import logger
from qcodes.instrument import IPInstrument, InstrumentBase

log = logging.getLogger(__name__)

Nanonis_LOGGER = ".".join((InstrumentBase.__module__, "com", "visa"))
CMD_NAME_FIELD_WIDTH = 32
HEADER_SIZE = 40
ERROR_STATUS_SIZE = 4
ERROR_LENGTH_SIZE = 4
ERROR_TRAILER_SIZE = ERROR_STATUS_SIZE + ERROR_LENGTH_SIZE
DEFAULT_TIMEOUT = float(0.1 * 60)
ARRAY_TYPES_REQUIRING_COUNT = {
    "1D array int",
    "1D array float32",
    "1D array float64",
    "1D array string",
}


class NanonisIPInstrumentbase(IPInstrument):
    def __init__(
        self,
        name: str,
        configpath: str,
        timeout: float = DEFAULT_TIMEOUT,
        command_configpath: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        # Connection settings remain in legacy/sigma.json. Command definitions
        # come exclusively from the canonical per-module JSON directory.
        self.configpath = configpath
        command_dir = (
            Path(command_configpath)
            if command_configpath
            else Path(__file__).resolve().parent.parent / "configs" / "commands"
        )
        self.command_list = self._load_command_directory(command_dir)
        self.commandList = self.command_list  # backwards compatibility

        self.config = self._load_command_list("sigma.json")
        self.TCP_info = self.get_TCP_info()

        super().__init__(
            name=name,
            address=self.TCP_info["IP-Adress"],
            port=int(self.TCP_info["Port"]),
            timeout=timeout,
            **kwargs,
        )
        self._buffer_size = 1024 * 1024
        self.nanonis_log = logger.get_instrument_logger(self, Nanonis_LOGGER)

    def _load_command_list(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(self.configpath, filename)
        with open(filepath, "r", encoding="utf-8") as cmd_file:
            return json.load(cmd_file)

    def _load_command_directory(self, path: Path) -> Dict[str, Any]:
        files = sorted(path.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No command JSON files found in {path}")

        commands: Dict[str, Any] = {}
        for file in files:
            with file.open("r", encoding="utf-8") as command_file:
                module_commands = json.load(command_file)
            duplicates = commands.keys() & module_commands.keys()
            if duplicates:
                names = ", ".join(sorted(duplicates))
                raise ValueError(f"Duplicate command definitions: {names}")
            commands.update(module_commands)
        return commands

    def loadCommandList(self, filename: str) -> Dict[str, Any]:
        """Backward-compatible camelCase wrapper."""
        return self._load_command_list(filename)

    def get_TCP_info(self) -> Dict[str, Any]:
        interface_cfg = self.config.get("Interface", {})
        ip_address = interface_cfg.get("IP-Adress")
        port = interface_cfg.get("Port")
        if ip_address is None or port is None:
            raise KeyError("Interface configuration missing 'IP-Adress' or 'Port'")

        log.info("Using Nanonis TCP connection %s:%s", ip_address, port)
        return {"IP-Adress": ip_address, "Port": port}

    def encode_request_message(
        self,
        cmd_name: str,
        arg_values: Mapping[str, Union[int, float, str, Sequence[Any]]],
        arg_types: Mapping[str, str],
    ) -> bytes:
        """Encodes a command including arguments into a byte array."""
        body = b""

        for key in arg_types:
            if key not in arg_values:
                raise KeyError(f"Missing value for argument '{key}' in command '{cmd_name}'")
            value = arg_values[key]
            type_code = arg_types[key]

            if type_code == "s":
                body += str(value).encode()
                continue

            if type_code.startswith("1D array "):
                sequence = self._ensure_sequence(value, key, cmd_name)
                element_type = type_code.split(" ", 2)[-1]

                if element_type == "int":
                    pack = int
                    fmt = "i"
                elif element_type == "float32":
                    pack = float
                    fmt = "f"
                elif element_type == "float64":
                    pack = float
                    fmt = "d"
                elif element_type == "string":
                    for element in sequence:
                        encoded = str(element).encode()
                        body += struct.pack(">i", len(encoded))
                        body += encoded
                    continue
                else:
                    raise ValueError(
                        f"Unsupported array type '{type_code}' for argument '{key}'"
                    )

                for element in sequence:
                    body += self.convert_number_to_byte(pack(element), fmt)
                continue

            body += self.convert_number_to_byte(value, type_code)

        cmd = self.convert_string_to_byte(cmd_name, CMD_NAME_FIELD_WIDTH)
        body_size = self.convert_number_to_byte(len(body), "i")
        send_response = self.convert_number_to_byte(1, "h")
        not_used = self.convert_number_to_byte(0, "h")
        return cmd + body_size + send_response + not_used + body

    def decodeResponseMessage(self, resp: bytes, respTypes: Mapping[str, str]) -> Dict[str, Any]:
        """Decodes a response message from the Nanonis software."""
        header_size = HEADER_SIZE
        index = header_size
        decoded_resp: Dict[str, Any] = {}
        for key, value in respTypes.items():
            size = len(self.convert_number_to_byte(0, value))
            decoded_resp[key] = self.convert_bytes_to_number(resp[index:index + size], value)
            index += size
        return decoded_resp

    def convert_string_to_byte(self, cmd: str, size: int) -> bytes:
        cmd_bytes = cmd.encode()
        if len(cmd_bytes) < size:
            cmd_bytes += bytes(size - len(cmd_bytes))
        return cmd_bytes

    def convert_number_to_byte(self, num: Any, numType: str) -> bytes:
        conv_format = f">{numType}"
        return struct.pack(conv_format, num)

    def convertNumberToByte(self, num: Any, numType: str) -> bytes:
        """Compatibility bridge for legacy camelCase usage."""
        return self.convert_number_to_byte(num, numType)

    def convert_bytes_to_number(self, numBytes: bytes, numType: str) -> Union[int, float]:
        conv_format = f">{numType}"
        return struct.unpack(conv_format, numBytes)[0]

    def encoded_cmd(self, cmd_name: str, cmdArgs: Sequence[Any]) -> bytes:
        if cmd_name not in self.commandList:
            raise RuntimeError(f"Command {cmd_name} is not in the command list")

        cmd_detail = self.commandList[cmd_name]
        arg_specs = self._arg_specs(cmd_detail)

        if len(cmdArgs) != len(arg_specs):
            raise ValueError(
                f"Command {cmd_name} needs {len(arg_specs)} arguments, but {len(cmdArgs)} given."
            )

        arg_values: Dict[str, Any] = {}
        prev_arg: Optional[str] = None

        for index, (arg_name, arg_type) in enumerate(arg_specs):
            coerced_value = self._coerce_argument(arg_type, cmdArgs[index], arg_name, cmd_name)
            arg_values[arg_name] = coerced_value

            if prev_arg and arg_type in ARRAY_TYPES_REQUIRING_COUNT:
                arg_values[prev_arg] = int(len(coerced_value))

            prev_arg = arg_name

        arg_types = {name: type_code for name, type_code in arg_specs}
        return self.encode_request_message(cmd_name=cmd_name, arg_values=arg_values, arg_types=arg_types)

    def _coerce_argument(
        self,
        arg_type: str,
        value: Any,
        arg_name: str,
        cmd_name: str,
    ) -> Any:
        try:
            if arg_type in {"I", "i", "H"}:
                return int(value)
            if arg_type in {"f", "d"}:
                return float(value)
            if arg_type == "s":
                return str(value)
            if arg_type in ARRAY_TYPES_REQUIRING_COUNT:
                sequence = self._ensure_sequence(value, arg_name, cmd_name)
                if arg_type == "1D array int":
                    return [int(item) for item in sequence]
                if arg_type == "1D array float32":
                    return [float(item) for item in sequence]
                if arg_type == "1D array float64":
                    return [float(item) for item in sequence]
                return [str(item) for item in sequence]
            return value
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Failed to coerce argument '{arg_name}' for command '{cmd_name}' to type '{arg_type}'"
            ) from error


    def _arg_specs(self, cmd_detail: Mapping[str, Any]) -> List[Tuple[str, str]]:
        specs: List[Tuple[str, str]] = []
        args = cmd_detail.get("args", [])
        type_lookup = cmd_detail.get("argTypes", {}) if isinstance(cmd_detail.get("argTypes"), Mapping) else {}

        if isinstance(args, list):
            for item in args:
                name: Optional[str] = None
                type_code: Optional[str] = None
                if isinstance(item, Mapping):
                    name = item.get("name")
                    type_code = item.get("type")
                elif isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
                    name, type_code = item[0], item[1]
                elif isinstance(item, str):
                    name = item
                    if isinstance(type_lookup, Mapping):
                        type_code = type_lookup.get(item)
                if name and type_code:
                    specs.append((str(name), str(type_code)))

        if not specs and isinstance(type_lookup, Mapping):
            for name, type_code in type_lookup.items():
                if name and type_code:
                    specs.append((str(name), str(type_code)))

        return specs

    def _resp_specs(self, cmd_detail: Mapping[str, Any]) -> List[Tuple[str, str]]:
        resp = cmd_detail.get("resp") or cmd_detail.get("respTypes", {})
        specs: List[Tuple[str, str]] = []
        if isinstance(resp, Mapping):
            for name, type_code in resp.items():
                if name and type_code:
                    specs.append((str(name), str(type_code)))
        elif isinstance(resp, list):
            for item in resp:
                if isinstance(item, Mapping):
                    name = item.get("name")
                    type_code = item.get("type")
                elif isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
                    name, type_code = item[0], item[1]
                else:
                    name = type_code = None
                if name and type_code:
                    specs.append((str(name), str(type_code)))
        return specs

    def _ensure_sequence(self, value: Any, arg_name: str, cmd_name: str) -> List[Any]:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (list, tuple)):
            return list(value)
        raise ValueError(
            f"Argument '{arg_name}' for command '{cmd_name}' should be a sequence, got {type(value)!r}."
        )

    def _send(self, encoded_message: bytes) -> None:
        if self._socket is None:
            raise RuntimeError(f"IPInstrument {self.name} is not connected")

        self.nanonis_log.debug("Writing %s to instrument %s", encoded_message, self.name)
        self._socket.sendall(encoded_message)

    def _recv_exactly(self, num_bytes: int) -> bytes:
        data = b""
        while len(data) < num_bytes:
            chunk = self._socket.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed prematurely")
            data += chunk
        return data

    def _recv(self) -> bytes:
        header = self._recv_exactly(HEADER_SIZE)
        body_size = int.from_bytes(header[32:36], byteorder="big")
        body = self._recv_exactly(body_size) if body_size > 0 else b""
        return header + body

    def write(self, cmd: str) -> None:
        head, args = self._parse_cli_command(cmd)
        try:
            self.write_raw(head, args)
        except Exception as exc:
            inst = repr(self)
            exc.args = exc.args + ("writing " + repr(cmd) + " to " + inst,)
            raise

    def ask(self, cmd: str) -> Any:
        head, args = self._parse_cli_command(cmd)
        try:
            return self.ask_raw(head, args)
        except Exception as exc:
            inst = repr(self)
            exc.args = exc.args + ("asking " + repr(cmd) + " to " + inst,)
            raise

    def _parse_cli_command(self, cmd: str) -> Tuple[str, List[Any]]:
        parts = self.split_command(cmd)
        if not parts:
            raise ValueError("Empty command string")
        return parts[0], parts[1:]

    def split_command(self, cmd: str) -> List[Any]:
        tokens = re.findall(r"\[[^\]]*\]|\S+", cmd)
        parsed_args: List[Any] = []
        for token in tokens:
            try:
                parsed_args.append(ast.literal_eval(token))
            except (ValueError, SyntaxError):
                parsed_args.append(token)
        return parsed_args

    def write_raw(self, cmd_name: str, cmdArgs: Sequence[Any]) -> None:
        encoded_cmd = self.encoded_cmd(cmd_name=cmd_name, cmdArgs=cmdArgs)
        with self._ensure_connection:
            self._send(encoded_cmd)
            response = self._recv()
            _, body = self._split_response(response)
            data, error_status, _, error_payload = self._split_body_and_error(body)
            if error_status:
                error_code, error_message = self.decode_error_message(error_payload)
                self.log_error(error_code, error_message)
                raise RuntimeError(error_message)
            if data:
                self.nanonis_log.debug("Unused response payload for write command %s: %s", cmd_name, data)

    def ask_raw(self, cmd_name: str, cmdArgs: Sequence[Any]) -> Union[Dict[str, Any], bytes]:
        encoded_cmd = self.encoded_cmd(cmd_name=cmd_name, cmdArgs=cmdArgs)
        with self._ensure_connection:
            self._send(encoded_cmd)
            response = self._recv()
            try:
                decode_response = self.parse_response_with_command_dict(response=response, cmd_name=cmd_name)
            except Exception as exc:
                log.exception("Failed to decode response for %s: %s", cmd_name, exc)
                return response
            checker_cmd_name = decode_response["cmd_name"]
            if checker_cmd_name != cmd_name:
                raise RuntimeError(
                    f"Wrong response command. {cmd_name} asked, but {checker_cmd_name} received."
                )
            return decode_response

    def _split_response(self, response: bytes) -> Tuple[str, bytes]:
        if len(response) < HEADER_SIZE:
            raise ValueError("Response shorter than header")
        cmd_name = response[:CMD_NAME_FIELD_WIDTH].decode("utf-8", errors="ignore").rstrip("\x00")
        body_size = int.from_bytes(response[32:36], byteorder="big")
        body = response[HEADER_SIZE:HEADER_SIZE + body_size]
        if len(body) != body_size:
            raise ValueError("Incomplete response body received")
        return cmd_name, body

    def _split_body_and_error(self, body: bytes) -> Tuple[bytes, int, int, bytes]:
        if len(body) < ERROR_TRAILER_SIZE:
            return body, 0, 0, b""
        payload_end = len(body) - ERROR_TRAILER_SIZE
        error_status = int.from_bytes(body[payload_end:payload_end + ERROR_STATUS_SIZE], byteorder="big")
        error_size = int.from_bytes(body[payload_end + ERROR_STATUS_SIZE:payload_end + ERROR_TRAILER_SIZE], byteorder="big")
        error_payload_start = max(payload_end - error_size, 0)
        error_payload = body[error_payload_start:payload_end]
        data = body[:error_payload_start]
        return data, error_status, error_size, error_payload

    def parse_response_with_command_dict(self, response: bytes, cmd_name: str) -> Dict[str, Any]:
        command_dict = self.commandList[cmd_name]
        response_cmd_name, body = self._split_response(response)

        if response_cmd_name != cmd_name:
            raise RuntimeError(
                f"Command name mismatch: expected {cmd_name}, got {response_cmd_name}"
            )

        payload, error_status, error_size_in_bytes, error_payload = self._split_body_and_error(body)

        if error_status:
            error_code, error_message = self.decode_error_message(error_payload)
            error_info = f"code={error_code} message={error_message}"
            log.error("Error response for %s: %s", cmd_name, error_info)
            raise RuntimeError(error_message)

        result: Dict[str, Any] = {
            "cmd_name": cmd_name,
            "body_size": len(payload),
            "error_size_in_bytes": error_size_in_bytes,
            "error_status": error_status,
        }

        offset = 0
        last_two_keys: List[Optional[str]] = [None, None]
        resp_specs = self._resp_specs(command_dict)

        for key, value_type in resp_specs:
            offset = self._decode_value(payload, offset, key, value_type, result, last_two_keys)

        return result

    def _decode_value(
        self,
        body: bytes,
        offset: int,
        key: str,
        value_type: str,
        result: Dict[str, Any],
        last_two_keys: List[Optional[str]],
    ) -> int:
        if len(value_type) == 1:
            if value_type == "s":
                length_key = last_two_keys[1]
                if length_key is None:
                    raise ValueError(f"Missing length key for string value '{key}'")
                str_length = int(result[length_key])
                value, offset = self.decode_string_with_length(body, offset, str_length)
            else:
                struct_format = ">" + value_type
                size = struct.calcsize(struct_format)
                value_bytes = body[offset:offset + size]
                if len(value_bytes) != size:
                    raise ValueError(f"Insufficient bytes to decode '{key}' as '{value_type}'")
                value, = struct.unpack(struct_format, value_bytes)
                offset += size
            result[key] = value
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "1D array string":
            length_key = last_two_keys[1]
            if length_key is None:
                raise ValueError(f"Cannot decode 1D string array for '{key}': missing length key")
            num_elements = int(result[length_key])
            strings, offset = self.decode_1d_array_string(body, offset, num_elements)
            result[key] = strings
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "2D array string":
            if not (last_two_keys[0] and last_two_keys[1]):
                raise ValueError(
                    f"Cannot decode 2D array string for key '{key}': missing row/col count in previous keys."
                )
            num_rows = int(result[last_two_keys[0]])
            num_cols = int(result[last_two_keys[1]])
            strings_2d, offset = self.decode_2d_array_string(body, offset, num_rows, num_cols)
            result[key] = strings_2d
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "2D array float32":
            if not (last_two_keys[0] and last_two_keys[1]):
                raise ValueError(
                    f"Cannot decode 2D array float32 for key '{key}': missing row/col count in previous keys."
                )
            num_rows = int(result[last_two_keys[0]])
            num_cols = int(result[last_two_keys[1]])
            array_2d, offset = self.decode_2d_array_num(body, offset, num_rows, num_cols, "f")
            result[key] = array_2d
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "1D array float32":
            length_key = last_two_keys[1]
            if length_key is None:
                raise ValueError(f"Cannot decode 1D array float32 for '{key}': missing length key")
            num_element = int(result[length_key])
            array_1d, offset = self.decode_2d_array_num(body, offset, 1, num_element, "f")
            result[key] = array_1d
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "1D array float64":
            length_key = last_two_keys[1]
            if length_key is None:
                raise ValueError(f"Cannot decode 1D array float64 for '{key}': missing length key")
            num_element = int(result[length_key])
            array_1d, offset = self.decode_2d_array_num(body, offset, 1, num_element, "d")
            result[key] = array_1d
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        if value_type == "1D array int":
            length_key = last_two_keys[1]
            if length_key is None:
                raise ValueError(f"Cannot decode 1D array int for '{key}': missing length key")
            num_element = int(result[length_key])
            array_1d, offset = self.decode_2d_array_num(body, offset, 1, num_element, "i")
            result[key] = array_1d
            last_two_keys[0] = last_two_keys[1]
            last_two_keys[1] = key
            return offset

        raise ValueError(f"Unsupported response type '{value_type}' for key '{key}'")

    def decode_string_with_length(self, body: bytes, offset: int, length: int) -> Tuple[str, int]:
        string_bytes = body[offset:offset + length]
        string_value = string_bytes.decode("utf-8", errors="replace")
        return string_value, offset + length

    def decode_1d_array_string(self, body: bytes, offset: int, num_elements: int) -> Tuple[List[str], int]:
        strings: List[str] = []
        for _ in range(num_elements):
            if offset + 4 > len(body):
                raise ValueError("Insufficient bytes while decoding string array length")
            string_size = struct.unpack(">i", body[offset:offset + 4])[0]
            offset += 4
            string_bytes = body[offset:offset + string_size]
            string_value = string_bytes.decode("utf-8", errors="replace")
            strings.append(string_value)
            offset += string_size
        return strings, offset

    def decode_2d_array_string(
        self,
        body: bytes,
        offset: int,
        rows: int,
        cols: int,
    ) -> Tuple[List[List[str]], int]:
        result_strings: List[List[str]] = []
        for _ in range(rows):
            row: List[str] = []
            for _ in range(cols):
                if offset + 4 > len(body):
                    raise ValueError("Insufficient bytes while decoding 2D string array length")
                length = int.from_bytes(body[offset:offset + 4], byteorder="big")
                offset += 4
                string_bytes = body[offset:offset + length]
                string_value = string_bytes.decode("utf-8", errors="replace")
                row.append(string_value)
                offset += length
            result_strings.append(row)
        return result_strings, offset

    def decode_2d_array_num(
        self,
        response: bytes,
        offset: int,
        num_rows: int,
        num_cols: int,
        fmt: str,
    ) -> Tuple[np.ndarray, int]:
        elem_size = struct.calcsize(f">{fmt}")
        dtype_map = {
            "f": np.float32,
            "d": np.float64,
            "i": np.int32,
            "I": np.uint32,
            "h": np.int16,
            "H": np.uint16,
        }
        dtype = dtype_map.get(fmt, np.float32)
        array_2d = np.empty((num_rows, num_cols), dtype=dtype)
        for row, col in product(range(num_rows), range(num_cols)):
            value_bytes = response[offset:offset + elem_size]
            if len(value_bytes) != elem_size:
                raise ValueError("Insufficient bytes while decoding numeric array")
            value, = struct.unpack(f">{fmt}", value_bytes)
            array_2d[row, col] = value
            offset += elem_size
        return array_2d, offset

    def decode_error_message(self, response_bytes: bytes) -> Tuple[int, str]:
        if len(response_bytes) >= 4:
            try:
                error_code = struct.unpack(">I", response_bytes[:4])[0]
                error_message_bytes = response_bytes[4:]
                error_message = error_message_bytes.decode("utf-8", errors="replace")
                return error_code, error_message
            except struct.error:
                pass
        if len(response_bytes) >= 28:
            try:
                error_code = struct.unpack(">I", response_bytes[24:28])[0]
                error_message_bytes = response_bytes[28:]
                error_message = error_message_bytes.decode("utf-8", errors="replace")
                return error_code, error_message
            except struct.error:
                pass
        return 0, response_bytes.decode("utf-8", errors="replace")

    def log_error(self, error_code: int, error_message: str) -> None:
        self.nanonis_log.error("Error Code: %s, Message: %s", error_code, error_message)
