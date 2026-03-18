from __future__ import annotations

from pathlib import Path

from aas_creo_bridge.app.context import init_log_store, init_aasx_registry, init_sync_manager, set_path_to_creoson, \
    init_creo_session_tracker, get_creo_session_tracker
from aas_creo_bridge.app.logging import setup_logging
from aas_creo_bridge.gui.main_window import MainWindow


def main() -> None:
    log_store = init_log_store()
    setup_logging(log_store)
    init_aasx_registry()
    init_sync_manager()
    set_path_to_creoson(Path(Path(__file__).parent.parent.parent.parent / "creoson"))  # hardcoded for now
    init_creo_session_tracker()
    get_creo_session_tracker().start_polling()
    window = MainWindow()
    window.run()
