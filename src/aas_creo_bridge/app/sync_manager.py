from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Optional

from aas_creo_bridge.adapters.aasx import AASXImportResult, group_models_by_version, filter_model_by_app, \
    ConsumingApplication, get_models_from_aas, FileData, Version
from aas_creo_bridge.app.context import get_aasx_registry

if TYPE_CHECKING:
    from typing import List

_logger = logging.getLogger(__name__)


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
        self._application = [ConsumingApplication("Creo Parametric", "12", "CREO12"),
                             ConsumingApplication("STEP", "AP242", "STEP-242")]
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

    def _model_sort_by_app(self, x) -> tuple[str, ...]:
        app_names = [app.application_name for app in self._application]
        app_priority = -app_names.index(x.consuming_applications[0].application_name)
        version_tuple = Version(x.consuming_applications[0].application_qualifier).to_tuple()
        return tuple(map(str, [app_priority, version_tuple]))

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

        # TODO: set creo version based on settings / config

        # TODO: select best fitting model Version -> Application -> file format
        m_grouped_by_version = group_models_by_version(models)

        sorted_keys = sorted(m_grouped_by_version.keys(), key=lambda x: Version(x).to_tuple(), reverse=True)

        m_filtered: dict[str, list[FileData]] = {}

        # Filter by Application
        for key in sorted_keys:
            models = m_grouped_by_version[key]
            m_filtered_by_app = filter_model_by_app(models, self._application, False)
            m_filtered_by_app = sorted(m_filtered_by_app, key=self._model_sort_by_app, reverse=True)
            if m_filtered_by_app:
                m_filtered[key] = m_filtered_by_app
                continue
            # TODO: filter by file format
            raise NotImplementedError

        best_model: Optional[FileData] = None

        for key in sorted_keys:
            if key not in m_filtered:
                _logger.warning(f"No model found for version {key}")
                continue
            best_model = m_filtered[key][0]

        print(best_model)

        # TODO: handle zip files
        # import_model_into_creo()


# Backwards-compatible name expected by app.context.init_sync_manager()
SyncManager = SynchronizationManager
