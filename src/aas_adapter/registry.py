from __future__ import annotations

import logging
import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from aas_adapter.importer import AASXImportResult

if typing.TYPE_CHECKING:
    from typing import Callable

_logger = logging.getLogger(__name__)

RegistryAction = Enum("RegistryAction", ["add", "remove"])


@dataclass
class AASXEntry:
    """
    An entry in the AASX registry containing the import result.

    :ivar result: The result of the AASX import.
    :type result: AASXImportResult
    """

    result: AASXImportResult


class AASXRegistry:
    """
    Keeps track of AASX packages the user opened/imported during the app session.

    This registry maintains mappings from both file paths and AAS identifiers to
    the imported AASX results. It also supports listeners to notify other
    components of changes in the registry.
    """

    def __init__(self) -> None:
        """
        Initialize an empty AASXRegistry.
        """
        self._by_path: dict[Path, AASXEntry] = {}
        self._by_id: dict[str, AASXEntry] = {}
        self._listeners: list[Callable[[RegistryAction, list[str]], None]] = []

    def register(self, result: AASXImportResult) -> None:
        """
        Register a new AASX import result.

        The result is indexed by its file path and all Asset Administration Shell
        identifiers it contains.

        :param result: The AASX import result to register.
        :type result: AASXImportResult
        """
        self._by_path[result.path] = AASXEntry(result=result)
        for aas_id in result.shells:
            self._by_id[aas_id] = AASXEntry(result=result)  # TODO: handle duplicates
        self._notify_listeners(RegistryAction.add, result.shells)

    def unregister(self, path: Path) -> None:
        """
        Unregister an AASX package by its path.

        Removes the package from the registry and notifies listeners.

        :param path: The path of the AASX file to unregister.
        :type path: Path
        """
        if path in self._by_path:
            shells = self._by_path[path].result.shells
            self._by_path.pop(path)
            for aas_id in self._by_path[path].result.shells:
                self._by_id.pop(aas_id)
            self._notify_listeners(RegistryAction.remove, shells)

    def is_open(self, key: Path | str) -> bool:
        """
        Check if an AASX package or an AAS identifier is currently open.

        :param key: Either the file path of the AASX or an AAS identifier.
        :type key: Path | str
        :return: True if the package or identifier is registered, False otherwise.
        :rtype: bool
        """
        if isinstance(key, Path):
            return key in self._by_path
        return key in self._by_id

    def list_by_path_open(self) -> list[AASXImportResult]:
        """
        Get all currently open AASX packages indexed by path.

        :return: A list of all imported results.
        :rtype: list[AASXImportResult]
        """
        return [entry.result for entry in self._by_path.values()]

    def list_by_id_open(self) -> list[AASXImportResult]:
        """
        Get all currently open AASX packages indexed by AAS identifier.

        :return: A list of all imported results.
        :rtype: list[AASXImportResult]
        """
        return [entry.result for entry in self._by_id.values()]

    def get(self, key: Path | str) -> AASXImportResult | None:
        """
        Retrieve an AASX import result by its path or an AAS identifier.

        :param key: Either the file path of the AASX or an AAS identifier.
        :type key: Path | str
        :return: The import result if found, None otherwise.
        :rtype: AASXImportResult | None
        """
        if isinstance(key, Path):
            entry = self._by_path.get(key)
        else:
            entry = self._by_id.get(key)
        return entry.result if entry else None

    def list_clear(self) -> None:
        """
        Clear all entries from the registry and notify listeners.
        """
        self._by_path.clear()
        self._by_id.clear()
        self._notify_listeners()

    def add_listener(self, listener: Callable[[RegistryAction, list[str]], None]) -> None:
        """Register a callback to be notified when the registry changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[RegistryAction, list[str]], None]) -> None:
        """Unregister a previously registered listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, action: str, aas_ids: list[str]) -> None:
        """Call all registered listeners."""
        for listener in self._listeners:
            try:
                listener(action, aas_ids)
            except Exception as e:
                _logger.error(
                    f"Error in AASXRegistry listener: {e}",
                    exc_info=True,
                )
