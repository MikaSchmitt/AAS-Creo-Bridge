from __future__ import annotations

import importlib

from aas_creo_bridge.adapters.creo import SetvarsConfigurationError

app_main = importlib.import_module("aas_creo_bridge.app.main")


def test_main_opens_settings_when_setvars_invalid(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _DummyLogger:
        def warning(self, *args, **kwargs) -> None:
            return None

    class _DummyWindow:
        def __init__(self, initial_view: str = "Home", startup_warning: str | None = None) -> None:
            captured["initial_view"] = initial_view
            captured["startup_warning"] = startup_warning

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(app_main, "init_log_store", lambda: object())
    monkeypatch.setattr(app_main, "setup_logging", lambda _store: None)
    monkeypatch.setattr(app_main, "get_logger", lambda _name=None: _DummyLogger())
    monkeypatch.setattr(app_main, "init_aasx_registry", lambda: None)
    monkeypatch.setattr(app_main, "init_sync_manager", lambda: None)
    monkeypatch.setattr(app_main, "set_path_to_creoson", lambda _path: None)
    monkeypatch.setattr(app_main, "ensure_setvars_exists", lambda: None)

    def _raise_setvars() -> None:
        raise SetvarsConfigurationError("setvars invalid")

    monkeypatch.setattr(app_main, "init_creo_session_tracker", _raise_setvars)
    monkeypatch.setattr(app_main, "MainWindow", _DummyWindow)

    app_main.main()

    assert captured["initial_view"] == "Settings"
    assert "setvars" in str(captured["startup_warning"]).lower()
    assert captured["ran"] is True


