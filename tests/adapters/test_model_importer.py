from __future__ import annotations

from pathlib import Path

import pytest

from aas_creo_bridge.adapters.creo.creo_connection import connect_to_creoson
from aas_creo_bridge.adapters.creo.model_import import import_model_into_creo


CREOSON_DIR = Path(r"C:\Users\T\Documents\PycharmProjects\AAS-Creo-Bridge\creoson")
ASM_PATH = Path(
    r"C:\OneDrive\Hochschule Karlsruhe\Entwicklungsprojekt - General\04_Beispieldateien\Pliers_Creo_Baugruppe\Tutorial 2 Pliers Parts\plier_mechanism.asm"
)
STEP_PATH = Path(
    r"C:\OneDrive\Hochschule Karlsruhe\Entwicklungsprojekt - General\04_Beispieldateien\GPLE60-3S\GPLE60-3S.stp"
)


@pytest.fixture(scope="module")
def creo_client():
    return connect_to_creoson(CREOSON_DIR)


def test_import_model_into_creo_raises_for_missing_path(tmp_path: Path, creo_client) -> None:
    missing = tmp_path / "missing.step"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        import_model_into_creo(creo_client, missing)


def test_import_model_into_creo_opens_native_asm(creo_client) -> None:
    assert import_model_into_creo(creo_client, ASM_PATH) is None


def test_import_model_into_creo_imports_step(creo_client) -> None:
    assert import_model_into_creo(creo_client, STEP_PATH) is None
