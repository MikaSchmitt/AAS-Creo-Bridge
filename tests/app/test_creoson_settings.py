from __future__ import annotations

from pathlib import Path

from aas_creo_bridge.adapters.creo import CreosonSettings, validate_setvars_bat, ensure_setvars_exists
from aas_creo_bridge.adapters.creo import DEFAULT_JSON_PORT, get_default_settings
from aas_creo_bridge.adapters.creo import save_creoson_settings, load_creoson_settings
from aas_creo_bridge.adapters.creo.config.defaults import sort_creo_common_paths_by_version


def test_save_and_load_creoson_settings_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("aas_creo_bridge.adapters.creo.config.paths.get_creoson_root", lambda: tmp_path)

    settings = CreosonSettings(
        proe_common="C:/Program Files/PTC/Creo 12.4.0.0/Common Files",
        proe_env="x86e_win64",
        java_home="jre",
        json_port=DEFAULT_JSON_PORT,
    )

    save_creoson_settings(settings)
    loaded = load_creoson_settings()

    assert loaded.proe_common == settings.proe_common
    assert loaded.proe_env == settings.proe_env
    assert loaded.java_home == settings.java_home
    assert loaded.json_port == DEFAULT_JSON_PORT


def test_ensure_setvars_exists_generates_batch_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("aas_creo_bridge.adapters.creo.config.paths.get_creoson_root", lambda: tmp_path)

    settings = CreosonSettings(
        proe_common="C:/Program Files/PTC/Creo 12.4.0.0/Common Files",
        proe_env="x86e_win64",
        java_home="jre",
        json_port=DEFAULT_JSON_PORT,
    )
    save_creoson_settings(settings)

    setvars_path = ensure_setvars_exists()

    assert setvars_path.exists()
    content = setvars_path.read_text(encoding="utf-8")
    assert "set PROE_COMMON=C:/Program Files/PTC/Creo 12.4.0.0/Common Files" in content
    assert "set PROE_ENV=x86e_win64" in content
    assert "set JAVA_HOME=jre" in content
    assert "set JSON_PORT=9056" in content


def test_default_java_home_prefers_embedded_jre(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "jre").mkdir()
    monkeypatch.setattr("aas_creo_bridge.adapters.creo.config.paths.get_creoson_root", lambda: tmp_path)

    detected_defaults = get_default_settings()

    assert detected_defaults.java_home == "jre"


def test_validate_setvars_bat_detects_missing_required_key(tmp_path: Path) -> None:
    setvars = tmp_path / "setvars.bat"
    setvars.write_text("set PROE_COMMON=C:/PTC\nset PROE_ENV=x86e_win64\n", encoding="utf-8")

    is_valid, error = validate_setvars_bat(setvars)

    assert not is_valid
    assert error is not None
    assert "JAVA_HOME" in error


def test_sort_creo_common_paths_by_version_orders_by_numeric_version() -> None:
    candidates = [
        Path("E:/Program Files/PTC/Creo 9.0.3.0/Common Files"),
        Path("E:/Program Files/PTC/Creo 10.0.0.0/Common Files"),
        Path("E:/Program Files/PTC/Creo 10.0.1.0/Common Files"),
    ]

    sorted_candidates = sort_creo_common_paths_by_version(candidates)

    assert str(sorted_candidates[-1].as_posix()).endswith("Creo 10.0.1.0/Common Files")
