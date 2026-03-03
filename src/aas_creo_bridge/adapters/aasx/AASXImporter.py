from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from basyx.aas import model
from basyx.aas.adapter import DictObjectStore, DictSupplementaryFileContainer, AASXReader
from pyecma376_2 import OPCCoreProperties

from aas_creo_bridge.app.context import get_logger

#from aas_test_engines import file

@dataclass(frozen=True)
class AASXImportResult:
    path: Path
    object_store: DictObjectStore
    file_store: DictSupplementaryFileContainer
    metadata: OPCCoreProperties | None
    thumbnail: bytes | None
    shells: list[str]


def import_aasx(path: Path) -> AASXImportResult:
    """
    Adapter entry point for importing an AASX package.

    For now this is a lightweight importer:
    - validates it's a readable zip
    - lists contained files
    - provides placeholder shell discovery hooks

    Replace `_discover_shells(...)` with real AAS parsing when available.
    """
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"AASX file not found: {path}")

    logger = get_logger()

    try:
        object_store = DictObjectStore()
        file_store = DictSupplementaryFileContainer()
        metadata = None
        thumbnail = None

        with AASXReader(path) as reader:
            identifiers = reader.read_into(object_store=object_store, file_store=file_store)
            metadata = reader.get_core_properties()
            thumbnail = reader.get_thumbnail()

        return AASXImportResult(
            path=path,
            object_store=object_store,
            file_store=file_store,
            metadata=metadata,
            thumbnail=thumbnail,
            shells=_discover_shells(identifiers, object_store),
        )
    except Exception as e:
        logger.error(f"AASX import failed for {path}: {e!r}")
        raise ValueError(f"Not a valid AASX/zip file: {path}") from e


def _discover_shells(identifiers: set[str], objects: model.AbstractObjectStore) -> list[str]:
    aas_shells = []

    logger = get_logger()

    if not identifiers or not objects:
        return []
    for identifier in identifiers:
        identifiable = objects.get_identifiable(identifier)
        if isinstance(identifiable, model.AssetAdministrationShell):
            logger.info(f"AssetAdministrationShell found {identifiable.id_short} {identifiable.id}")
            aas_shells.append(identifier)
    return aas_shells
