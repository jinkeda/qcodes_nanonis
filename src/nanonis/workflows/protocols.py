"""Structural client contracts used by workflows."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CommandClient(Protocol):
    def send(
        self, command: str, *args: Any, timeout: float | None = None
    ) -> Any: ...


@runtime_checkable
class RecoverableCommandClient(CommandClient, Protocol):
    def reconnect(self) -> None: ...

