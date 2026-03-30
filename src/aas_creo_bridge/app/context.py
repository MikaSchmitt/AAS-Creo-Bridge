from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from creopyson.exceptions import MissingKey

from aas_creo_bridge.adapters import connect_to_creoson, CreoSessionTracker
from aas_creo_bridge.app.logging import LogStore
from creopyson import Client

if TYPE_CHECKING:
    from aas_adapter import AASXRegistry
    from aas_creo_bridge.app.sync_manager import SynchronizationManager

_log_store: LogStore | None = None
_aasx_registry: AASXRegistry | None = None
_sync_manager: SynchronizationManager | None = None
_creoson_client: Client | None = None
_path_to_creoson: Path | None = None
_creo_session_tracker: CreoSessionTracker | None = None


def init_log_store() -> LogStore:
    global _log_store
    if _log_store is None:
        _log_store = LogStore()
    return _log_store


def get_log_store() -> LogStore:
    return init_log_store()


def get_logger(name: str | None = None) -> logging.Logger:
    base_name = "aas_creo_bridge"
    if name:
        return logging.getLogger(f"{base_name}.{name}")
    return logging.getLogger(base_name)


def init_aasx_registry() -> AASXRegistry:
    global _aasx_registry
    if _aasx_registry is None:
        from aas_adapter import AASXRegistry

        _aasx_registry = AASXRegistry()
    return _aasx_registry


def get_aasx_registry() -> AASXRegistry:
    return init_aasx_registry()


def init_sync_manager() -> SynchronizationManager:
    global _sync_manager
    if _sync_manager is None:
        from aas_creo_bridge.app.sync_manager import SynchronizationManager

        _sync_manager = SynchronizationManager()
    return _sync_manager


def get_sync_manager() -> SynchronizationManager:
    return init_sync_manager()


def set_path_to_creoson(path: Path) -> None:
    global _path_to_creoson
    _path_to_creoson = path


def get_creoson_client() -> Client | None:
    global _creoson_client
    global _path_to_creoson

    if _creoson_client:
        try:
            _creoson_client.connect()
        except (RuntimeError, ConnectionError, MissingKey):
            _creoson_client = None

    if not _creoson_client:
        _creoson_client = connect_to_creoson(_path_to_creoson)

    return _creoson_client


def init_creo_session_tracker() -> None:
    global _creo_session_tracker
    if _creo_session_tracker is None:
        client = get_creoson_client()
        if client is None:
            logger = get_logger(__name__)
            logger.error("Unable to initialize CreoSessionTracker: Creoson client is unavailable.")
            raise RuntimeError("Creoson client is unavailable; cannot initialize CreoSessionTracker.")
        _creo_session_tracker = CreoSessionTracker(client=client, poll_interval_seconds=1)
        _creo_session_tracker.initialize()
        _creo_session_tracker.refresh()


def get_creo_session_tracker() -> CreoSessionTracker:
    if not _creo_session_tracker:
        init_creo_session_tracker()
    return _creo_session_tracker
