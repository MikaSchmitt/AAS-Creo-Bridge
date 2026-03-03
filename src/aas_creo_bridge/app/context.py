from __future__ import annotations

from typing import TYPE_CHECKING

from aas_creo_bridge.app.logging import AppLogger

if TYPE_CHECKING:
    from aas_creo_bridge.app.aasx_registry import AASXRegistry

_logger: AppLogger | None = None
_aasx_registry: AASXRegistry | None= None

def init_logger() -> AppLogger:
    global _logger
    if _logger is None:
        _logger = AppLogger()
    return _logger

def get_logger() -> AppLogger:
    return init_logger()

def init_aasx_registry() -> AASXRegistry:
    global _aasx_registry
    if _aasx_registry is None:
        from aas_creo_bridge.app.aasx_registry import AASXRegistry

        _aasx_registry = AASXRegistry()
    return _aasx_registry

def get_aasx_registry() -> AASXRegistry:
    return init_aasx_registry()