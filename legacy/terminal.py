import ast
import os
import shlex
import sys
from typing import Any, List, Mapping, Sequence, Tuple

from PyQt5.QtGui import QColor, QTextCharFormat, QCloseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from Nanonis_ipinstrumentbase import NanonisIPInstrumentbase

COLOR_MAP = {
    "black": QColor("black"),
    "gray": QColor("gray"),
    "red": QColor("red"),
}
SEPARATOR = "-" * 40


class NanonisTerminal(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.instrument = self._create_instrument()
        self._init_ui()

    def _create_instrument(self) -> NanonisIPInstrumentbase:
        config_path = os.path.dirname(os.path.abspath(__file__))
        return NanonisIPInstrumentbase(
            name="nanonis",
            configpath=config_path,
            timeout=100,
        )

    def _init_ui(self) -> None:
        self.setWindowTitle("Nanonis Terminal")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter Nanonis Command:"))

        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_command)
        layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_command)
        layout.addWidget(send_button)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setLayout(layout)

    def send_command(self) -> None:
        user_input = self._pop_input()
        if user_input is None:
            return

        if self._request_close(user_input):
            self.close()
            return

        self._echo_user_input(user_input)

        try:
            command, args = self._parse_command(user_input)
        except ValueError as error:
            self._append_text(f"Error: {error}", color="red")
            self._append_separator()
            return

        self._dispatch_command(command, args)
        self._append_separator()

    def _pop_input(self) -> str | None:
        user_input = self.input_field.text().strip()
        self.input_field.clear()
        return user_input or None

    def _request_close(self, user_input: str) -> bool:
        return user_input.lower() in {"exit", "quit"}

    def _echo_user_input(self, user_input: str) -> None:
        self._append_text(f"> {user_input}")

    def _parse_command(self, user_input: str) -> Tuple[str, List[Any]]:
        parts = shlex.split(user_input)
        if not parts:
            raise ValueError("No command provided.")

        command, raw_args = parts[0], parts[1:]
        args = [self._coerce_arg(arg) for arg in raw_args]
        return command, args

    def _coerce_arg(self, value: str) -> Any:
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    def _dispatch_command(self, command: str, args: List[Any]) -> None:
        try:
            response = self.instrument.ask_raw(command, args)
            self._render_response(response)
        except Exception as error:
            self._append_text(f"Error: {error}", color="red")

    def _render_response(self, response: Any) -> None:
        if response is None:
            self._append_text("(no response)", color="gray")
            return

        if isinstance(response, Mapping):
            for key, value in response.items():
                self._append_text(f"{key}: {value}")
            return

        if isinstance(response, Sequence) and not isinstance(response, (str, bytes, bytearray)):
            for item in response:
                self._append_text(str(item))
            return

        self._append_text(str(response))

    def _append_separator(self) -> None:
        self._append_text(SEPARATOR, color="gray")
        self.output_area.moveCursor(self.output_area.textCursor().End)

    def _append_text(self, text: str, color: str = "black") -> None:
        cursor = self.output_area.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(COLOR_MAP.get(color, COLOR_MAP["black"]))
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        print("Closing Nanonis connection...")
        try:
            if self.instrument is not None:
                self.instrument.close()
                print("Nanonis connection closed.")
        except Exception as error:
            print(f"Error while closing Nanonis: {error}")
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    terminal = NanonisTerminal()
    terminal.resize(600, 400)
    terminal.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
