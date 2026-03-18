import logging
import re

import creopyson

from .bom_component_export import get_assembly_data
from .types import Parameter, PartParameters

_logger = logging.getLogger(__name__)


def update_parameter(
        client: creopyson.Client,
        part_parameters: PartParameters,
) -> None:
    part_name: str = part_parameters.file_name

    if not client.is_creo_running():
        raise RuntimeError("Creo is not running.")

    if not client.file_exists(part_name):
        raise FileNotFoundError(f"Part file not found in Creo: {part_name}")

    for param in part_parameters.parameters:
        try:
            client.parameter_set(
                file_=part_name,
                name=param.name,
                value=param.value,
                type_=param.type,
                designate=True,  # Designate the parameter so it can be used in PDM and BOM
            )
            _logger.info("Updated %s -> %s: %s", part_name, param.name, param.value)
        except Exception as e:
            _logger.error(
                "Could not set parameter %s for %s: %r",
                param.name,
                part_name,
                e,
                exc_info=True,
            )


def bulk_update_parameters(
        client: creopyson.Client,
        parts_with_parameters: list[PartParameters],
) -> None:
    errors: str = ""
    for part_parameters in parts_with_parameters:
        try:
            update_parameter(client, part_parameters)
        except Exception as e:
            errors += f"    {str(e)} \n"
    if errors:
        raise RuntimeError(f"Failed to set {len(errors)} parameter(s):\n{errors}")


def update_parameters_from_list(
        client: creopyson.Client,
        parts_with_parameters: list[PartParameters],
        model_name: str | None = None,
) -> None:
    """
    Reads the assembly structure from Creo and updates parameters based on a list
    of part_parameters entries.
    """

    if not parts_with_parameters:
        raise ValueError("No part parameter data provided.")

    # Map normalized file name -> list of parameters to write.
    parameter_map: dict[str, list[Parameter]] = {}
    for part in parts_with_parameters:
        normalized_name = re.sub(r"\.\d+$", "", part.file_name).strip().lower()
        parameter_map[normalized_name] = part.parameters

    target = model_name or "<active>"
    _logger.info("Scanning assembly structure for: %s", target)
    assembly_data = get_assembly_data(
        client,
        file_=model_name,
        paths=True,
        skeletons=False,
        top_level=False,
        get_transforms=False,
        exclude_inactive=False,
        get_simpreps=False,
        include_parameters=True,
        include_mass_props=False,
        include_bounding_box=True,
    )
    components = set(assembly_data.index)

    if not components:
        raise RuntimeError("No components found or error during BOM extraction.")

    updates_done = 0
    errors: list[str] = []

    def _collect_existing_params(tree: object) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = {}

        def _walk(node: object) -> None:
            if isinstance(node, list):
                for item in node:
                    _walk(item)
                return
            if not isinstance(node, dict):
                return
            file_name = node.get("file")
            if file_name:
                meta = node.get("metadata") or {}
                params = meta.get("parameters") or []
                names: set[str] = set()
                for item in params:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("param_name") or item.get("parameter_name")
                        if name:
                            names.add(str(name).upper())
                if names:
                    mapping[str(file_name)] = names
            children = node.get("children")
            if children is not None:
                _walk(children)

        _walk(tree)
        return mapping

    existing_param_map = _collect_existing_params(assembly_data.get("assembly_tree"))

    for comp in components:
        comp_clean = re.sub(r"\.\d+$", "", comp).lower()
        if comp_clean not in parameter_map:
            continue

        existing_param_names = existing_param_map.get(comp, set())

        for param in parameter_map[comp_clean]:
            if param.name.upper() in existing_param_names:
                _logger.info("Skipping %s -> %s (already exists)", comp, param.name)
                continue
            try:
                client.parameter_set(
                    file_=comp,
                    name=param.name,
                    value=param.value,
                    type_=param.type,
                    designate=True,
                )
                _logger.info("Updated %s -> %s: %s", comp, param.name, param.value)
                updates_done += 1
            except Exception as e:
                _logger.error(
                    "Could not set parameter %s for %s: %r",
                    param.name,
                    comp,
                    e,
                    exc_info=True,
                )
                errors.append(f"{comp}:{param.name}")

    _logger.info("Process finished. Successfully updated %s parameters.", updates_done)

    if errors:
        raise RuntimeError(
            f"Failed to set {len(errors)} parameter(s). First error: {errors[0]}"
        )
