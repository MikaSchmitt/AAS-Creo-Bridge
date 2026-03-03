from __future__ import annotations

from typing import TYPE_CHECKING
import logging

from aas_creo_bridge.app.logging import LogStore

if TYPE_CHECKING:
    from aas_creo_bridge.app.aasx_registry import AASXRegistry

_log_store: LogStore | None = None
_aasx_registry: AASXRegistry | None= None

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
        from aas_creo_bridge.app.aasx_registry import AASXRegistry

        _aasx_registry = AASXRegistry()
    return _aasx_registry

def get_aasx_registry() -> AASXRegistry:
    return init_aasx_registry()