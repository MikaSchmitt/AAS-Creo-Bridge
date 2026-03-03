from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Callable


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str

    def format(self, *, with_timestamp: bool = True) -> str:
        if with_timestamp:
            ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            return f"[{ts}] {self.level}: {self.message}"
        return f"{self.level}: {self.message}"


LogListener = Callable[[LogEntry], None]

@dataclass
class AppLogger:
    """
    Simple in-memory application logger.

    - Stores log entries (timestamp + level + message)
    - Allows listeners (e.g. UI) to be notified on new entries
    - Exposes formatted string lines for simple UIs
    """
    _entries: list[LogEntry] = field(default_factory=list)
    _listeners: list[LogListener] = field(default_factory=list)

    @property
    def entries(self) -> list[LogEntry]:
        # Return a copy so callers can't mutate internal state accidentally.
        return list(self._entries)

    @property
    def lines(self) -> list[str]:
        return [e.format(with_timestamp=True) for e in self._entries]

    @property
    def last_message(self) -> str:
        return self._entries[-1].message if self._entries else ""

    def subscribe(self, listener: LogListener) -> None:
        self._listeners.append(listener)

    def log(self, message: str, *, level: LogLevel = LogLevel.INFO) -> LogEntry:
        entry = LogEntry(timestamp=datetime.now(), level=level, message=message)
        self._entries.append(entry)
        for listener in self._listeners:
            listener(entry)
        return entry

    def debug(self, message: str) -> LogEntry:
        return self.log(message, level=LogLevel.DEBUG)

    def info(self, message: str) -> LogEntry:
        return self.log(message, level=LogLevel.INFO)

    def warning(self, message: str) -> LogEntry:
        return self.log(message, level=LogLevel.WARNING)

    def error(self, message: str) -> LogEntry:
        return self.log(message, level=LogLevel.ERROR)

    def clear(self) -> None:
        self._entries.clear()