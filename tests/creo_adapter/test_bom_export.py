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
ASM_PATH = Path(
    r"C:\OneDrive\Hochschule Karlsruhe\Entwicklungsprojekt - General\04_Beispieldateien\Pliers_Creo_Baugruppe\Tutorial 2 Pliers Parts\plier_mechanism.asm.23"
)


@pytest.fixture(scope="module")
def creo_client():
    return connect_to_creoson(CREOSON_DIR)


def test_bom_export_writes_bom_to_file(creo_client) -> None:
    import_model_into_creo(creo_client, ASM_PATH)
    part = PartParameters(
        file_name="ARM_TOP.PRT",
        parameters=[
            Parameter(name="assetID", type="string", value="423828319"),
            Parameter(name="OrderCodeofManufacturer", type="string", value="OCM-001"),
        ],
    )
    set_part_parameters(creo_client, part)

    asm_file = re.sub(r"\.\d+$", "", ASM_PATH.name)
    bom = get_assembly_data(creo_client, file_=asm_file, include_parameters=True)

    export_path = Path(__file__).resolve().parent / "bom_export.json"
    export_path.write_text(json.dumps(asdict(bom), indent=2, ensure_ascii=True), encoding="utf-8")

    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").strip()
