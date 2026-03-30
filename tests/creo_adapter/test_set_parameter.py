from __future__ import annotations

from pathlib import Path

import pytest

from aas_creo_bridge.adapters.creo_connection import connect_to_creoson
from aas_creo_bridge.adapters.model_import import import_model_into_creo
from aas_creo_bridge.adapters.set_parameter import set_part_parameters
from aas_creo_bridge.adapters.types import Parameter, PartParameters

CREOSON_DIR = Path(__file__).resolve().parents[2] / "creoson"
ASM_PATH = Path(__file__).resolve().parents[2] / "tests/fixtures/creo_test_asm/suction_gripper.asm.1"


@pytest.fixture(scope="module")
def creo_client():
    return connect_to_creoson(CREOSON_DIR)


@pytest.mark.integration
def test_set_part_parameters_sets_parameter(creo_client) -> None:
    import_model_into_creo(creo_client, ASM_PATH)
    part = PartParameters(
        file_name="SUCTION_PLATE.PRT",
        parameters=[
            Parameter(name="assetID", type="string", value="fictitiousAssetID1234567"),
            Parameter(name="OrderCodeofManufacturer", type="string", value="fictitiousCodeofManufacturer1234567"),
        ],
    )
    assert set_part_parameters(creo_client, part) is None
