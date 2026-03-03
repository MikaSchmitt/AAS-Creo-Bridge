from __future__ import annotations

import logging
import typing
import traceback
from dataclasses import dataclass
from pathlib import Path

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult

if typing.TYPE_CHECKING:
    from typing import Callable

_logger = logging.getLogger(__name__)

@dataclass
class AASXEntry:
    result: AASXImportResult


class AASXRegistry:
    """
    Keeps track of AASX packages the user opened/imported during the app session.
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, AASXEntry] = {}
        self._by_id: dict[str, AASXEntry] = {}
        self._listeners: list[Callable[[], None]] = []

    def register(self, result: AASXImportResult) -> None:
        self._by_path[result.path] = AASXEntry(result=result)
        for aas_id in result.shells:
            self._by_id[aas_id] = AASXEntry(result=result)  # TODO: handle duplicates
        self._notify_listeners()

    def unregister(self, path: Path) -> None:
        if path in self._by_path:
            self._by_path.pop(path)
            self._notify_listeners()

    def is_open(self, path: Path) -> bool:
        return path in self._by_path

    def is_open(self, aas_id: str) -> bool:
        return aas_id in self._by_id

    def list_by_path_open(self) -> list[AASXImportResult]:
        return [entry.result for entry in self._by_path.values()]

    def list_by_id_open(self) -> list[AASXImportResult]:
        return [entry.result for entry in self._by_id.values()]

    def get(self, path: Path) -> AASXImportResult | None:
        entry = self._by_path.get(path)
        return entry.result if entry else None

    def get(self, aas_id: str) -> AASXImportResult | None:
        entry = self._by_id.get(aas_id)
        return entry.result if entry else None

    def list_clear(self) -> None:
        self._by_path.clear()
        self._by_id.clear()
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
                _logger.error(f"Error in AASXRegistry listener: {e}", exc_info=traceback.format_exc())