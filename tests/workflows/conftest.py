from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from nanonis.protocol import TransportState


class FakeController:
    def __init__(self) -> None:
        self.sent: list[tuple[str, tuple[Any, ...], float | None]] = []
        self._responses: dict[str, deque[Any]] = defaultdict(deque)
        self._failures: dict[str, deque[BaseException]] = defaultdict(deque)
        self.transport_state = TransportState.READY
        self.is_connected = True

    def script(self, command: str, *responses: Any) -> "FakeController":
        self._responses[command].extend(responses)
        return self

    def fail(self, command: str, *errors: BaseException) -> "FakeController":
        self._failures[command].extend(errors)
        return self

    def send(
        self, command: str, *args: Any, timeout: float | None = None
    ) -> Any:
        self.sent.append((command, args, timeout))
        if self._failures[command]:
            raise self._failures[command].popleft()
        if self._responses[command]:
            value = self._responses[command].popleft()
            return value(command, args, timeout) if callable(value) else value
        return None


class RecoverableFakeController(FakeController):
    def __init__(self) -> None:
        super().__init__()
        self.reconnect_count = 0
        self.reconnect_error: BaseException | None = None

    def reconnect(self) -> None:
        self.reconnect_count += 1
        if self.reconnect_error is not None:
            raise self.reconnect_error
        self.transport_state = TransportState.READY
        self.is_connected = True

