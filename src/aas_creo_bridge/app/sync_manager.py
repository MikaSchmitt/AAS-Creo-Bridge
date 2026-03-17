from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from aas_adapter import ConsumingApplication, get_global_asset_id, get_models_from_aas, select_best_model, \
    materialize_model_file, RegistryAction
from aas_creo_bridge.adapters.creo import import_model_into_creo, update_parameter, PartParameters, Parameter
from aas_creo_bridge.app.context import get_aasx_registry, get_creoson_client

if TYPE_CHECKING:
    from typing import List

_logger = logging.getLogger(__name__)


@dataclass
class ConnectionLink:
    aas_shell_id: str | None = None
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


class SynchronizationManager:
    def __init__(self) -> None:
        self._file_format = None
        self._application = [ConsumingApplication("Creo Parametric", "12", "CREO12"),
                             ConsumingApplication("STEP", "AP242", "STEP-242")]
        self._links_by_aas_id: dict[str, ConnectionLink] = {}
        self._links_by_creo_model: dict[str, ConnectionLink] = {}
        self.out_dir = Path(tempfile.mkdtemp(prefix="aas_creo_bridge_"))

        get_aasx_registry().add_listener(self._on_registry_changed)

    def link(self, aas_shell_id: str | None, creo_model_name: str | None) -> None:

        link = self._links_by_aas_id.get(aas_shell_id, None)
        if link and link.creo_model_name == creo_model_name:
            return
        elif link and link.creo_model_name != creo_model_name:
            raise RuntimeError(f"AAS shell {aas_shell_id} is already linked")

        link = self._links_by_creo_model.get(creo_model_name)
        if link and link.aas_shell_id == aas_shell_id:
            return
        elif link and link.aas_shell_id != aas_shell_id:
            raise RuntimeError(f"Creo model {creo_model_name} is already linked")

        if aas_shell_id:
            self._links_by_aas_id[aas_shell_id] = ConnectionLink(aas_shell_id, creo_model_name)

        if creo_model_name:
            self._links_by_creo_model[creo_model_name] = ConnectionLink(aas_shell_id, creo_model_name)

    def unlink(self, key: str) -> None:
        if key in self._links_by_aas_id:
            conn = self._links_by_aas_id.pop(key)
            self._links_by_creo_model.pop(conn.creo_model_name)
            return
        if key in self._links_by_creo_model:
            conn = self._links_by_creo_model.pop(key)
            self._links_by_aas_id.pop(conn.aas_shell_id)
            return

    def unlink_all(self) -> None:
        self._links_by_aas_id.clear()
        self._links_by_creo_model.clear()

    def list_links(self) -> List[ConnectionLink]:
        return list(self._links_by_aas_id.values())

    def get_link_by_aas_id(self, aas_shell_id: str) -> ConnectionLink | None:
        return self._links_by_aas_id.get(aas_shell_id)

    def get_link_by_creo_model(self, creo_model_name: str) -> ConnectionLink | None:
        return self._links_by_aas_id.get(creo_model_name)

    def sync_aas_to_creo(self, aas_id: str) -> None:
        aasx = get_aasx_registry().get(aas_id)
        if aasx is None:
            _logger.error("No AASX registry entry found for AAS shell %s", aas_id)
            return None

        try:
            models = get_models_from_aas(aasx, aas_id)
            best = select_best_model(models, self._application, self._file_format)

            if best is None:
                _logger.warning("No suitable model found for AAS shell %s", aas_id)
                return None

            prepared = materialize_model_file(aasx, best, self.out_dir)
            if prepared is None:
                _logger.warning("Model materialization returned no result for AAS shell %s", aas_id)
                return None

            _logger.info("Prepared model extracted to %s", prepared.extracted_path)
        except ValueError as exc:
            _logger.error(
                "Failed to synchronize AAS shell %s to Creo due to invalid AAS data: %s",
                aas_id,
                exc,
            )
            _logger.debug("Exception while syncing AAS shell %s", aas_id, exc_info=True)
            return None

        client = get_creoson_client()
        model_name = import_model_into_creo(client, prepared.extracted_path)

        # aas_id is the unique identifier for the AAS instance
        global_asset_id = get_global_asset_id(aasx, aas_id)  # unique identifier for the AAS type

        part_with_params = PartParameters(
            model_name,
            [
                Parameter(
                    "AAS_ID",
                    "string",
                    aas_id
                ),
                Parameter(
                    "GLOBAL_ASSET_ID",
                    "string",
                    global_asset_id
                ),
            ]
        )

        try:
            update_parameter(client, part_with_params)
        except Exception as exc:
            _logger.error(
                "Failed to set parameters for model %s: %s",
                model_name,
                exc,
            )
            _logger.debug("Exception while setting parameters", exc_info=True)

        self.link(aas_id, model_name)

        return None

    def _on_registry_changed(self, action: str, shells: list[str]):
        if action == RegistryAction.add:
            for shell in shells:
                self.link(shell, None)
        elif action == RegistryAction.remove:
            for shell in shells:
                self.unlink(shell)
