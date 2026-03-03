from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult
from aas_creo_bridge.adapters.aasx.get_models import get_models_from_aas, ConsumingApplication, find_model_for_app
from aas_creo_bridge.adapters.creo.model_importer import import_model_into_creo
from aas_creo_bridge.app.context import get_aasx_registry

if TYPE_CHECKING:
    from typing import List

@dataclass
class ConnectionLink:
    aas_shell_id: str
    creo_model_name: str | None = None


class CreoModelDefinition:
    def __init__(self, source_aas_shell_id: str, model_name: str):
        self._source_aas_shell_id = source_aas_shell_id
        self._model_name = model_name

    @property
    def source_aas_shell_id(self) -> str:
        return self._source_aas_shell_id

    @property
    def model_name(self) -> str:
        return self._model_name


class ModelExtractor(Protocol):
    def extract_model(self, aas_shell_id: str) -> CreoModelDefinition: ...


class CreoAdapter(Protocol):
    def create_model(self, definition: CreoModelDefinition) -> None: ...


class SynchronizationManager:
    def __init__(self) -> None:
        self._links: dict[str, ConnectionLink] = {}
        self._extractor: ModelExtractor | None = None
        self._creo_adapter: CreoAdapter | None = None

    def set_extractor(self, extractor: ModelExtractor) -> None:
        self._extractor = extractor

    def set_creo_adapter(self, creo_adapter: CreoAdapter) -> None:
        self._creo_adapter = creo_adapter

    def link(self, aas_shell_id: str, creo_model_name: str | None) -> None:
        self._links[aas_shell_id] = ConnectionLink(aas_shell_id, creo_model_name)

    def list_links(self) -> List[ConnectionLink]:
        return list(self._links.values())

    def sync_aas_to_creo(self, aas_shell_id: str) -> None:
        # Preferred/testable path (used by your unit tests)
        if self._extractor is not None and self._creo_adapter is not None:
            extracted = self._extractor.extract_model(aas_shell_id)
            self._creo_adapter.create_model(extracted)
            self.link(aas_shell_id, extracted.model_name)
            return

        # Fallback path (current implementation hooks)
        aasx_registry = get_aasx_registry()
        aasx: AASXImportResult = aasx_registry.get(aas_shell_id)
        models = get_models_from_aas(aasx, aas_shell_id)

        find_model_for_app(models, [ConsumingApplication("Creo", "12", "Creo 12"), ConsumingApplication("STEP", "AP312", "Step-2.14")])


        # TODO: select best fitting model
        # TODO: handle zip files
        #import_model_into_creo()


# Backwards-compatible name expected by app.context.init_sync_manager()
SyncManager = SynchronizationManager
