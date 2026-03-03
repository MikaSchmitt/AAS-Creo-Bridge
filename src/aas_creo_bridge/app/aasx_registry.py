from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aas_creo_bridge.adapters.aasx.AASXImporter import AASXImportResult


@dataclass
class AASXEntry:
    result: AASXImportResult


class AASXRegistry:
    """
    Keeps track of AASX packages the user opened/imported during the app session.
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, AASXEntry] = {}

    def register(self, result: AASXImportResult) -> None:
        self._by_path[result.path] = AASXEntry(result=result)

    def unregister(self, path: Path) -> None:
        self._by_path.pop(path, None)

    def is_open(self, path: Path) -> bool:
        return path in self._by_path

    def list_open(self) -> list[AASXImportResult]:
        return [entry.result for entry in self._by_path.values()]

    def get(self, path: Path) -> AASXImportResult | None:
        entry = self._by_path.get(path)
        return entry.result if entry else None
