"""Exceptions raised by the typed Nanonis command layer."""

from ..protocol.exceptions import NanonisError


class NanonisArgumentError(NanonisError, ValueError):
    """A command argument contradicts its declared wire-size relationship."""

    def __init__(
        self,
        command: str,
        field: str,
        expected: object,
        actual: object,
        *,
        data_field: str | None = None,
    ) -> None:
        self.command = command
        self.field = field
        self.expected = expected
        self.actual = actual
        self.data_field = data_field
        target = f" for {data_field!r}" if data_field else ""
        super().__init__(
            f"Command {command!r} field {field!r}{target} must be "
            f"{expected!r}, got {actual!r}"
        )
