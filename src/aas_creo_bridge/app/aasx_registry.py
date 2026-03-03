from __future__ import annotations

import typing
import traceback
from dataclasses import dataclass
from pathlib import Path

from aas_creo_bridge.adapters.aasx.AASXImporter import AASXImportResult
from aas_creo_bridge.app.context import get_logger

if typing.TYPE_CHECKING:
    from typing import Callable


@dataclass
class AASXEntry:
    result: AASXImportResult


class AASXRegistry:
    """
    Keeps track of AASX packages the user opened/imported during the app session.
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, AASXEntry] = {}
        self._listeners: list[Callable[[], None]] = []

    def register(self, result: AASXImportResult) -> None:
        self._by_path[result.path] = AASXEntry(result=result)
        self._notify_listeners()

    def unregister(self, path: Path) -> None:
        if path in self._by_path:
            self._by_path.pop(path)
            self._notify_listeners()

    def is_open(self, path: Path) -> bool:
        return path in self._by_path

    def list_open(self) -> list[AASXImportResult]:
        return [entry.result for entry in self._by_path.values()]

    def get(self, path: Path) -> AASXImportResult | None:
        entry = self._by_path.get(path)
        return entry.result if entry else None

    def list_clear(self) -> None:
        self._by_path.clear()
        self._notify_listeners()

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Register a callback to be notified when the registry changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]) -> None:
        """Unregister a previously registered listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Call all registered listeners."""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                logger = get_logger()
                logger.error(f"Error in AASXRegistry listener: {e}", exc_info=traceback.format_exc())