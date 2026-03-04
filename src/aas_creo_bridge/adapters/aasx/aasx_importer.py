from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from basyx.aas import model
from basyx.aas.adapter import DictObjectStore, DictSupplementaryFileContainer, AASXReader
from pyecma376_2 import OPCCoreProperties



_logger = logging.getLogger(__name__)


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
    Import an AASX file and extract relevant information including objects, supplementary
    files, metadata, and a thumbnail, if available. The method validates the file's
    existence, reads its contents, and processes it into a structured format suitable
    for further usage.

    :param path: Path of the AASX file to be imported
    :type path: Path
    :return: An instance of AASXImportResult containing the imported data such as object
        store, supplementary file store, metadata, thumbnail, and the list of discovered
        shells
    :rtype: AASXImportResult
    :raises FileNotFoundError: If the specified AASX file does not exist or is not
        accessible
    :raises ValueError: If the AASX file is invalid or does not conform to the expected
        format
    """
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"AASX file not found: {path}")

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
        _logger.error(f"AASX import failed for {path}: {e!r}", exc_info=True)
        raise ValueError(f"Not a valid AASX/zip file: {path}") from e


def _discover_shells(identifiers: set[str], objects: model.AbstractObjectStore) -> list[str]:
    aas_shells = []

    if not identifiers or not objects:
        return []
    for identifier in identifiers:
        identifiable = objects.get_identifiable(identifier)
        if isinstance(identifiable, model.AssetAdministrationShell):
            _logger.info(f"AssetAdministrationShell found {identifiable.id_short} {identifiable.id}")
            aas_shells.append(identifier)
    return aas_shells
