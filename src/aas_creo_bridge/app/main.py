from __future__ import annotations

from aas_creo_bridge.gui.main_window import MainWindow
from aas_creo_bridge.app.context import init_logger, init_aasx_registry

def main() -> None:
    init_logger()
    init_aasx_registry()
    window = MainWindow()
    window.run()