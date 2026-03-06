import re

import creopyson

from .types import parameter, part_parameters
from .get_bom import get_creo_bom


def update_parameters_from_list(
    client: creopyson.Client,
    model_name: str,
    parts_with_parameters: list[part_parameters],
) -> None:
    """
    Reads the assembly structure from Creo and updates parameters based on a list
    of part_parameters entries.
    """

    if not parts_with_parameters:
        print("No part parameter data provided.")
        return

    # Map normalized file name -> list of parameters to write.
    parameter_map: dict[str, list[parameter]] = {}
    for part in parts_with_parameters:
        normalized_name = re.sub(r"\.\d+$", "", part.file_name).strip().lower()
        parameter_map[normalized_name] = part.parameters

    print(f"Scanning assembly structure for: {model_name}")
    components = get_creo_bom(client, model_name)

    if not components:
        print("No components found or error during BOM extraction.")
        return

    updates_done = 0
    for comp in components:
        comp_clean = re.sub(r"\.\d+$", "", comp).lower()
        if comp_clean not in parameter_map:
            continue

        for param in parameter_map[comp_clean]:
            try:
                client.parameter_set(
                    file_=comp,
                    name=param.parameter_name,
                    value=param.value,
                    type_=param.type,
                    designate=True,
                )
                print(f"  [OK] {comp} -> {param.parameter_name}: {param.value}")
                updates_done += 1
            except Exception as e:
                print(f"  [ERROR] Could not set parameter {param.parameter_name} for {comp}: {e}")

    print(f"Process finished. Successfully updated {updates_done} parameters.")
