from __future__ import annotations

from pathlib import Path

import pytest

from aas_creo_bridge.adapters.creo.model_importer import import_model_into_creo


def test_import_model_into_creo_raises_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.step"
    with pytest.raises(ValueError, match="does not exist"):
        import_model_into_creo(missing, ".step")


def test_import_model_into_creo_accepts_native_prt_and_asm(tmp_path: Path) -> None:
    file_path = tmp_path / "part.prt"
    file_path.write_text("x", encoding="utf-8")

    assert import_model_into_creo(file_path, "prt") is None
    assert import_model_into_creo(file_path, "asm") is None


def test_import_model_into_creo_accepts_supported_exchange_formats(tmp_path: Path) -> None:
    file_path = tmp_path / "part.step"
    file_path.write_text("x", encoding="utf-8")

    assert import_model_into_creo(file_path, ".stp") is None
    assert import_model_into_creo(file_path, ".step") is None
    assert import_model_into_creo(file_path, ".pvz") is None
    assert import_model_into_creo(file_path, ".pvs") is None


def test_import_model_into_creo_currently_rejects_igs_iges_neu(tmp_path: Path) -> None:
    file_path = tmp_path / "part.exchange"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported target format"):
        import_model_into_creo(file_path, ".igs")
    with pytest.raises(ValueError, match="Unsupported target format"):
        import_model_into_creo(file_path, ".iges")
    with pytest.raises(ValueError, match="Unsupported target format"):
        import_model_into_creo(file_path, ".neu")


def test_import_model_into_creo_raises_for_unsupported_format(tmp_path: Path) -> None:
    file_path = tmp_path / "part.unknown"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported target format"):
        import_model_into_creo(file_path, ".xyz", target_format="creo")
