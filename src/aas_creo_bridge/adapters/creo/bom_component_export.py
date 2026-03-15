from __future__ import annotations

import logging
from typing import Any

import creopyson

from .types import CreoBom, CreoEntity, Parameter

_logger = logging.getLogger(__name__)

def _get_seq_path(node: dict[str, Any]) -> str | None:
    for key in ("seq_path", "path", "seqpath"):
        value = node.get(key)
        if value:
            return str(value)
    return None


def _get_file_name(node: dict[str, Any]) -> str | None:
    for key in ("file", "file_name", "name"):
        value = node.get(key)
        if value:
            return str(value)
    return None


def _to_parameters(raw_params: list[dict[str, Any]] | None) -> list[Parameter]:
    if not raw_params:
        return []
    params: list[Parameter] = []
    for item in raw_params:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("param_name") or item.get("parameter_name")
        if not name:
            continue
        params.append(
            Parameter(
                name=str(name),
                type=str(item.get("type") or ""),
                value=item.get("value"),
            )
        )
    return params


def _build_entity_tree(bom_res: dict[str, Any]) -> CreoBom:
    root_file = str(bom_res.get("file") or "")
    root = CreoEntity(file_name=root_file, seq_path="root", level=0)
    index: dict[str, CreoEntity] = {"root": root}

    def _build_from_node(node: dict[str, Any]) -> CreoEntity | None:
        file_name = _get_file_name(node)
        seq_path = _get_seq_path(node)
        if not file_name or not seq_path:
            _logger.warning("Skipping BOM node with missing file/seq_path: %s", node)
            return None

        level = node.get("level")
        if not isinstance(level, int):
            level = seq_path.count(".")

        entity = CreoEntity(
            file_name=file_name,
            seq_path=seq_path,
            level=level,
            transform_matrix=node.get("transform"),
        )
        index[seq_path] = entity

        for child_node in node.get("children") or []:
            if not isinstance(child_node, dict):
                continue
            child_entity = _build_from_node(child_node)
            if child_entity:
                entity.add_child(child_entity)
        return entity

    for child in bom_res.get("children") or []:
        if not isinstance(child, dict):
            continue
        child_entity = _build_from_node(child)
        if child_entity:
            root.add_child(child_entity)

    return CreoBom(root=root, index=index)


def get_assembly_data(
    client: creopyson.Client,
    file_: str | None = None,
    *,
    paths: bool = True,
    skeletons: bool = False,
    top_level: bool = False,
    get_transforms: bool = False,
    exclude_inactive: bool = False,
    get_simpreps: bool = False,
    include_parameters: bool = False,
    include_mass_props: bool = False,
    include_bounding_box: bool = False,
) -> CreoBom:
    """
    Fetch an assembly BOM and return it as a structured entity tree with index.
    """
    try:
        bom_res = client.bom_get_paths(
            file_=file_,
            paths=paths,
            skeletons=skeletons,
            top_level=top_level,
            get_transforms=get_transforms,
            exclude_inactive=exclude_inactive,
            get_simpreps=get_simpreps,
        )
    except Exception as exc:
        _logger.error("Failed to fetch BOM from Creo: %r", exc, exc_info=True)
        raise RuntimeError("Failed to fetch BOM from Creo.") from exc

    bom = _build_entity_tree(bom_res)

    _enrich_entities(
        client,
        bom,
        include_parameters=include_parameters,
        include_mass_props=include_mass_props,
        include_bounding_box=include_bounding_box,
    )
    return bom


def _enrich_entities(
    client: creopyson.Client,
    bom: CreoBom,
    *,
    include_parameters: bool,
    include_mass_props: bool,
    include_bounding_box: bool,
) -> None:
    parameter_cache: dict[str, list[Parameter]] = {}
    mass_cache: dict[str, dict[str, Any]] = {}
    bbox_cache: dict[str, dict[str, Any]] = {}

    for entity in bom.index.values():
        file_name = entity.file_name
        if not file_name:
            continue

        if include_parameters:
            if file_name not in parameter_cache:
                try:
                    raw_params = client.parameter_list(file_=file_name)
                    parameter_cache[file_name] = _to_parameters(raw_params)
                except Exception as exc:
                    _logger.error("Creoson API error for '%s': %r", file_name, exc, exc_info=True)
                    raise RuntimeError(f"Creoson API error for '{file_name}'") from exc
            entity.parameters = list(parameter_cache[file_name])

        if include_mass_props:
            if file_name not in mass_cache:
                try:
                    mass_cache[file_name] = client.file_massprops(file_=file_name) or {}
                except Exception as exc:
                    _logger.error("Creoson API error for '%s': %r", file_name, exc, exc_info=True)
                    raise RuntimeError(f"Creoson API error for '{file_name}'") from exc
            mass_props = mass_cache[file_name]
            entity.mass = float(mass_props.get("mass") or 0.0)
            entity.volume = float(mass_props.get("volume") or 0.0)

        if include_bounding_box:
            if file_name not in bbox_cache:
                try:
                    bbox_cache[file_name] = client.geometry_bound_box(file_=file_name) or {}
                except Exception as exc:
                    _logger.error("Creoson API error for '%s': %r", file_name, exc, exc_info=True)
                    raise RuntimeError(f"Creoson API error for '{file_name}'") from exc
            bbox = bbox_cache[file_name]
            try:
                entity.length = float(bbox.get("max_x", 0.0)) - float(bbox.get("min_x", 0.0))
                entity.width = float(bbox.get("max_y", 0.0)) - float(bbox.get("min_y", 0.0))
                entity.height = float(bbox.get("max_z", 0.0)) - float(bbox.get("min_z", 0.0))
            except Exception:
                _logger.warning("Invalid bounding box data for '%s': %s", file_name, bbox)


def get_assembly_component_files(client: creopyson.Client, target_model: str) -> set[str]:
    """
    Return only unique component file names from an assembly (minimal mode).
    """
    bom = get_assembly_data(
        client,
        file_=target_model,
        paths=True,
        skeletons=False,
        top_level=False,
        get_transforms=False,
        exclude_inactive=False,
        get_simpreps=False,
    )
    return {entity.file_name for entity in bom.index.values() if entity.file_name}
