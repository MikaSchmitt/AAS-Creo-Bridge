from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Callable, TYPE_CHECKING


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
    exc_info: str | None = None

    def format(self, *, with_timestamp: bool = True) -> str:
        msg = f"{self.level}: {self.message}"
        if with_timestamp:
            ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            msg = f"[{ts}] {msg}"
        if self.exc_info:
            msg += f"\n{self.exc_info}"
        return msg


LogListener = Callable[[LogEntry], None]


@dataclass
class LogStore:
    """
    Simple in-memory store for log entries.
    """
    _entries: list[LogEntry] = field(default_factory=list)
    _listeners: list[LogListener] = field(default_factory=list)

    @property
    def entries(self) -> list[LogEntry]:
        return list(self._entries)

    @property
    def lines(self) -> list[str]:
        return [e.format(with_timestamp=True) for e in self._entries]

    @property
    def last_message(self) -> str:
        return self._entries[-1].message if self._entries else ""

    def subscribe(self, listener: LogListener) -> None:
        self._listeners.append(listener)

    def add(self, message: str, level: LogLevel, exc_info: str | None = None) -> LogEntry:
        entry = LogEntry(timestamp=datetime.now(), level=level, message=message, exc_info=exc_info)
        self._entries.append(entry)
        for listener in self._listeners:
            listener(entry)
        return entry

    def clear(self) -> None:
        self._entries.clear()


class AppLogHandler(logging.Handler):
    """
    Standard logging handler that redirects all records to a LogStore instance.
    """

    def __init__(self, log_store: LogStore) -> None:
        super().__init__()
        self._log_store = log_store

    def emit(self, record: logging.LogRecord) -> None:
        level_map = {
            logging.DEBUG: LogLevel.DEBUG,
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARNING,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.ERROR,
        }
        level = level_map.get(record.levelno, LogLevel.INFO)
        message = f"{record.name}: {record.getMessage()}"

        exc_info = None
        if record.exc_info:
            exc_info = "".join(traceback.format_exception(*record.exc_info))

        self._log_store.add(message, level=level, exc_info=exc_info)


def setup_logging(log_store: LogStore) -> None:
    """
    Configures the standard logging library to use our LogStore.
    """
    handler = AppLogHandler(log_store)
    root_logger = logging.getLogger("aas_creo_bridge")
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)