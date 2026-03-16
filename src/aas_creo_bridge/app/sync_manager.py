from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from aas_adapter import ConsumingApplication, get_models_from_aas, select_best_model, materialize_model_file
from aas_creo_bridge.adapters.creo import import_model_into_creo
from aas_creo_bridge.app.context import get_aasx_registry, get_creoson_client

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


class SynchronizationManager:
    def __init__(self) -> None:
        self._file_format = None
        self._application = [ConsumingApplication("Creo Parametric", "12", "CREO12"),
                             ConsumingApplication("STEP", "AP242", "STEP-242")]
        self._links: dict[str, ConnectionLink] = {}
        self.out_dir = Path(tempfile.mkdtemp(prefix="aas_creo_bridge_"))

    def link(self, aas_shell_id: str, creo_model_name: str | None) -> None:
        self._links[aas_shell_id] = ConnectionLink(aas_shell_id, creo_model_name)

    def unlink(self, aas_shell_id: str) -> None:
        del self._links[aas_shell_id]

    def unlink_all(self) -> None:
        self._links.clear()

    def list_links(self) -> List[ConnectionLink]:
        return list(self._links.values())

    def sync_aas_to_creo(self, aas_shell_id: str) -> None:
        aasx = get_aasx_registry().get(aas_shell_id)
        if aasx is None:
            _logger.error("No AASX registry entry found for AAS shell %s", aas_shell_id)
            return None

        try:
            models = get_models_from_aas(aasx, aas_shell_id)
            best = select_best_model(models, self._application, self._file_format)

            if best is None:
                _logger.warning("No suitable model found for AAS shell %s", aas_shell_id)
                return None

            prepared = materialize_model_file(aasx, best, self.out_dir)
            if prepared is None:
                _logger.warning("Model materialization returned no result for AAS shell %s", aas_shell_id)
                return None

            _logger.info("Prepared model extracted to %s", prepared.extracted_path)
        except ValueError as exc:
            _logger.error(
                "Failed to synchronize AAS shell %s to Creo due to invalid AAS data: %s",
                aas_shell_id,
                exc,
            )
            _logger.debug("Exception while syncing AAS shell %s", aas_shell_id, exc_info=True)
            return None

        client = get_creoson_client()
        import_model_into_creo(client, prepared.extracted_path)
        return None
