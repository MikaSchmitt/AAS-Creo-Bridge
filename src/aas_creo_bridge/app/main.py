from __future__ import annotations

from aas_creo_bridge.gui.main_window import MainWindow
from aas_creo_bridge.app.context import init_log_store, init_aasx_registry
from aas_creo_bridge.app.logging import setup_logging

def main() -> None:
    log_store = init_log_store()
    setup_logging(log_store)
    init_aasx_registry()
    window = MainWindow()
    window.run()