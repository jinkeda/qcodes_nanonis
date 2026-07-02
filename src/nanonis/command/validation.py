"""Materialize, infer, and validate typed Nanonis command arguments."""

from __future__ import annotations

import operator
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np

from .encoder import CommandEncoder
from .exceptions import NanonisArgumentError
from .registry import ArgDefinition, CommandDefinition, VariableLengthConstraint


_INTEGER_BOUNDS = {
    'int16': (-(2**15), 2**15 - 1),
    'int32': (-(2**31), 2**31 - 1),
    'uint16': (0, 2**16 - 1),
    'uint32': (0, 2**32 - 1),
}


class CommandArgumentValidator:
    """Validate wire-size relationships before a typed command is serialized."""

    def validate_positional(
        self,
        command: CommandDefinition,
        values: tuple[Any, ...],
    ) -> tuple[Any, ...]:
        if len(values) != len(command.send_args):
            raise NanonisArgumentError(
                command.name,
                'arguments',
                len(command.send_args),
                len(values),
            )
        materialized = {
            arg.name: self._materialize(command.name, arg, value)
            for arg, value in zip(command.send_args, values)
        }
        self._validate_constraints(command, materialized, inferred=set())
        return tuple(materialized[arg.name] for arg in command.send_args)

    def materialize_named(
        self,
        command: CommandDefinition,
        values: Mapping[str, Any],
    ) -> tuple[Any, ...]:
        fields = {arg.name: arg for arg in command.send_args}
        unknown = sorted(set(values) - set(fields))
        if unknown:
            raise NanonisArgumentError(
                command.name, 'fields', f"known fields {sorted(fields)}", unknown
            )

        derived = self._derived_fields(command.send_constraints.values())
        missing = sorted(set(fields) - set(values) - derived)
        if missing:
            raise NanonisArgumentError(
                command.name, 'fields', 'all non-derived fields', missing
            )

        materialized = {
            name: self._materialize(command.name, fields[name], value)
            for name, value in values.items()
        }
        inferred = derived - set(values)
        self._validate_constraints(command, materialized, inferred=inferred)
        return tuple(materialized[arg.name] for arg in command.send_args)

    @staticmethod
    def _derived_fields(
        constraints: Iterable[VariableLengthConstraint],
    ) -> set[str]:
        return {
            value
            for constraint in constraints
            for value in (
                constraint.count,
                constraint.byte_size,
                constraint.rows,
                constraint.columns,
            )
            if value is not None
        }

    def _materialize(
        self, command: str, arg: ArgDefinition, value: Any
    ) -> Any:
        if not (arg.type.startswith('array_') or arg.type.startswith('matrix_')):
            return value
        if isinstance(value, (str, bytes, bytearray)):
            raise NanonisArgumentError(
                command, arg.name, 'an array value', type(value).__name__
            )
        if isinstance(value, np.ndarray):
            materialized = value
        else:
            try:
                materialized = list(value)
            except TypeError as exc:
                raise NanonisArgumentError(
                    command, arg.name, 'an iterable array value', type(value).__name__
                ) from exc

        if arg.type.startswith('array_'):
            if arg.type == 'array_string':
                if any(not isinstance(item, (str, bytes)) for item in materialized):
                    raise NanonisArgumentError(
                        command, arg.name, 'only str or bytes elements', materialized
                    )
                return list(materialized)
            array = np.asarray(materialized)
            if array.ndim != 1:
                raise NanonisArgumentError(
                    command, arg.name, 'a one-dimensional array', array.shape
                )
            return materialized

        if arg.type == 'matrix_string':
            rows = [list(row) for row in materialized]
            widths = {len(row) for row in rows}
            if len(widths) > 1:
                raise NanonisArgumentError(
                    command, arg.name, 'a rectangular matrix', sorted(widths)
                )
            if any(
                not isinstance(item, (str, bytes))
                for row in rows
                for item in row
            ):
                raise NanonisArgumentError(
                    command, arg.name, 'only str or bytes elements', rows
                )
            return rows

        array = np.asarray(materialized)
        if array.ndim != 2:
            raise NanonisArgumentError(
                command, arg.name, 'a two-dimensional matrix', array.shape
            )
        return materialized

    def _validate_constraints(
        self,
        command: CommandDefinition,
        values: dict[str, Any],
        *,
        inferred: set[str],
    ) -> None:
        arg_types = {arg.name: arg.type for arg in command.send_args}
        for constraint in command.send_constraints.values():
            data = values[constraint.field]
            if constraint.count:
                self._set_or_check(
                    command.name,
                    values,
                    inferred,
                    constraint.count,
                    len(data),
                    constraint.field,
                    arg_types,
                )
            if constraint.byte_size:
                self._set_or_check(
                    command.name,
                    values,
                    inferred,
                    constraint.byte_size,
                    CommandEncoder.encoded_string_array_size(data),
                    constraint.field,
                    arg_types,
                )
            if constraint.rows or constraint.columns:
                shape = np.asarray(data, dtype=object).shape
                if len(shape) != 2:
                    raise NanonisArgumentError(
                        command.name, constraint.field, 'a matrix', shape
                    )
                if constraint.rows:
                    self._set_or_check(
                        command.name,
                        values,
                        inferred,
                        constraint.rows,
                        shape[0],
                        constraint.field,
                        arg_types,
                    )
                if constraint.columns:
                    self._set_or_check(
                        command.name,
                        values,
                        inferred,
                        constraint.columns,
                        shape[1],
                        constraint.field,
                        arg_types,
                    )

    def _set_or_check(
        self,
        command: str,
        values: dict[str, Any],
        inferred: set[str],
        size_field: str,
        expected: int,
        data_field: str,
        arg_types: Mapping[str, str],
    ) -> None:
        self._check_integer_range(command, size_field, expected, arg_types[size_field])
        if size_field in inferred and size_field not in values:
            values[size_field] = expected
            return
        try:
            actual = operator.index(values[size_field])
        except (KeyError, TypeError) as exc:
            raise NanonisArgumentError(
                command,
                size_field,
                expected,
                values.get(size_field),
                data_field=data_field,
            ) from exc
        self._check_integer_range(command, size_field, actual, arg_types[size_field])
        if actual != expected:
            raise NanonisArgumentError(
                command,
                size_field,
                expected,
                actual,
                data_field=data_field,
            )

    @staticmethod
    def _check_integer_range(
        command: str, field: str, value: int, dtype: str
    ) -> None:
        lower, upper = _INTEGER_BOUNDS[dtype]
        if not lower <= value <= upper:
            raise NanonisArgumentError(
                command, field, f"an integer in [{lower}, {upper}]", value
            )
