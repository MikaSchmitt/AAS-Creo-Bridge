from __future__ import annotations

from pathlib import Path

import creopyson
import pytest

from aas_creo_bridge.adapters.creo.creo_connection import connect_to_creoson
from aas_creo_bridge.adapters.creo.model_import import import_model_into_creo

CREOSON_DIR = Path(__file__).resolve().parents[2] / "creoson"
ASM_PATH = Path(__file__).resolve().parents[1] / "fixtures/creo_test_asm/suction_gripper.asm.1"
STEP_PATH = Path(__file__).resolve().parents[1] / "fixtures/GPLE60-3S.stp"


@pytest.fixture(scope="module")
def creo_client():
    return connect_to_creoson(CREOSON_DIR)


def clear_session(creo_client: creopyson.Client):
    creo_client.file_close_window()
    creo_client.file_erase_not_displayed()


@pytest.mark.integration
def test_import_model_into_creo_raises_for_missing_path(tmp_path: Path, creo_client) -> None:
    missing = tmp_path / "missing.step"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        import_model_into_creo(creo_client, missing)


@pytest.mark.integration
def test_import_model_into_creo_opens_native_asm(creo_client) -> None:
    clear_session(creo_client)
    assert import_model_into_creo(creo_client, ASM_PATH) is None


@pytest.mark.integration
def test_import_model_into_creo_imports_step(creo_client) -> None:
    clear_session(creo_client)
    assert import_model_into_creo(creo_client, STEP_PATH) is None
