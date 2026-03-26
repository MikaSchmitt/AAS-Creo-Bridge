from __future__ import annotations

from pathlib import Path

from aas_creo_bridge import config
from aas_creo_bridge.config import defaults, paths
from aas_creo_bridge.config import CreosonSettings, DEFAULT_JSON_PORT


def test_save_and_load_creoson_settings_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "get_creoson_root", lambda: tmp_path)

    settings = CreosonSettings(
        proe_common="C:/Program Files/PTC/Creo 12.4.0.0/Common Files",
        proe_env="x86e_win64",
        java_home="jre",
        json_port=DEFAULT_JSON_PORT,
    )

    config.save_creoson_settings(settings)
    loaded = config.load_creoson_settings()

    assert loaded.proe_common == settings.proe_common
    assert loaded.proe_env == settings.proe_env
    assert loaded.java_home == settings.java_home
    assert loaded.json_port == DEFAULT_JSON_PORT


def test_ensure_setvars_exists_generates_batch_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "get_creoson_root", lambda: tmp_path)

    settings = CreosonSettings(
        proe_common="C:/Program Files/PTC/Creo 12.4.0.0/Common Files",
        proe_env="x86e_win64",
        java_home="jre",
        json_port=DEFAULT_JSON_PORT,
    )
    config.save_creoson_settings(settings)

    setvars_path = config.ensure_setvars_exists()

    assert setvars_path.exists()
    content = setvars_path.read_text(encoding="utf-8")
    assert "set PROE_COMMON=C:/Program Files/PTC/Creo 12.4.0.0/Common Files" in content
    assert "set PROE_ENV=x86e_win64" in content
    assert "set JAVA_HOME=jre" in content
    assert "set JSON_PORT=9056" in content


def test_default_java_home_prefers_embedded_jre(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "jre").mkdir()
    monkeypatch.setattr(defaults, "get_creoson_root", lambda: tmp_path)

    detected_defaults = config.get_default_settings()

    assert detected_defaults.java_home == "jre"


def test_validate_setvars_bat_detects_missing_required_key(tmp_path: Path) -> None:
    setvars = tmp_path / "setvars.bat"
    setvars.write_text("set PROE_COMMON=C:/PTC\nset PROE_ENV=x86e_win64\n", encoding="utf-8")

    is_valid, error = config.validate_setvars_bat(setvars)

    assert not is_valid
    assert error is not None
    assert "JAVA_HOME" in error


