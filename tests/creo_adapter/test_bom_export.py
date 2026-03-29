from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

import pytest

from aas_creo_bridge.adapters.creo.bom_export import get_assembly_data
from aas_creo_bridge.adapters.creo.creo_connection import connect_to_creoson
from aas_creo_bridge.adapters.creo.model_import import import_model_into_creo
from aas_creo_bridge.adapters.creo.set_parameter import set_part_parameters
from aas_creo_bridge.adapters.creo.types import Parameter, PartParameters

CREOSON_DIR = Path(__file__).resolve().parents[2] / "creoson"
ASM_PATH = Path(__file__).resolve().parents[1] / "fixtures/creo_test_asm/suction_gripper.asm.1"


@pytest.fixture(scope="module")
def creo_client():
    return connect_to_creoson(CREOSON_DIR)


@pytest.mark.integration
def test_bom_export_writes_bom_to_file(creo_client) -> None:
    import_model_into_creo(creo_client, ASM_PATH)
    part = PartParameters(
        file_name="SUCTION_PLATE.PRT",
        parameters=[
            Parameter(name="assetID", type="string", value="fictitiousAssetID1234567"),
            Parameter(name="OrderCodeofManufacturer", type="string", value="fictitiousCodeofManufacturer1234567"),
        ],
    )
    set_part_parameters(creo_client, part)

    asm_file = re.sub(r"\.\d+$", "", ASM_PATH.name)
    bom = get_assembly_data(
        creo_client,
        file_=asm_file,
        include_parameters=True,
        include_mass_props=True,
        include_bounding_box=True,
        get_transforms=True,
    )

    export_path = Path(__file__).resolve().parents[1] / "fixtures/bom_export.json"
    actual_path = Path(__file__).resolve().parents[1] / "fixtures/bom_export.actual.json"
    actual_json = json.dumps(asdict(bom), indent=2, ensure_ascii=True)
    actual_path.write_text(actual_json, encoding="utf-8")
    assert actual_json == export_path.read_text(encoding="utf-8").strip()
