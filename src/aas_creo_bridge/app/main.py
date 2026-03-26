from __future__ import annotations

from pathlib import Path

from aas_creo_bridge.adapters.creo import SetvarsConfigurationError
from aas_creo_bridge.app.context import init_log_store, init_aasx_registry, init_sync_manager, set_path_to_creoson, \
    init_creo_session_tracker, get_creo_session_tracker, get_logger
from aas_creo_bridge.app.logging import setup_logging
from aas_creo_bridge.config import ensure_setvars_exists
from aas_creo_bridge.gui.main_window import MainWindow


def main() -> None:
    log_store = init_log_store()
    setup_logging(log_store)
    logger = get_logger(__name__)
    init_aasx_registry()
    init_sync_manager()
    set_path_to_creoson(Path(Path(__file__).parent.parent.parent.parent / "creoson"))  # hardcoded for now
    ensure_setvars_exists()

    initial_view = "Home"
    startup_warning: str | None = None

    try:
        init_creo_session_tracker()
        get_creo_session_tracker().start_polling()
    except SetvarsConfigurationError as exc:
        logger.warning("CREOSON startup blocked by invalid setvars configuration.", exc_info=True)
        initial_view = "Settings"
        startup_warning = f"CREOSON settings are invalid. Please update Settings.\n\n{exc}"
    except RuntimeError:
        logger.warning("CREOSON is not ready. Open Settings to configure setvars.bat and reconnect.", exc_info=True)
        initial_view = "Settings"
        startup_warning = "CREOSON is not ready. Please open Settings and verify your CREOSON configuration."

    window = MainWindow(initial_view=initial_view, startup_warning=startup_warning)
    window.run()
