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


def _iter_child_nodes(node: dict[str, Any]) -> list[dict[str, Any]]:
    children = node.get("children")
    if isinstance(children, dict):
        return [children]
    if isinstance(children, list):
        return [item for item in children if isinstance(item, dict)]
    return []


def _resolve_root_node(bom_res: dict[str, Any]) -> dict[str, Any] | None:
    children = bom_res.get("children")
    if isinstance(children, dict):
        return children
    if any(key in bom_res for key in ("file", "seq_path", "children")):
        return bom_res
    return None


def _build_entity_tree(bom_res: dict[str, Any], *, get_transforms: bool) -> CreoBom:
    root_node = _resolve_root_node(bom_res)
    bom_file = str(bom_res.get("file") or "")
    root_file = str((root_node or {}).get("file") or bom_file or "")
    if bom_file and root_file and bom_file != root_file:
        _logger.warning(
            "BOM root file mismatch: bom_res.file=%s root_node.file=%s",
            bom_file,
            root_file,
        )
    root_seq_path = _get_seq_path(root_node or {}) or str(bom_res.get("seq_path") or "root")
    root = CreoEntity(file_name=root_file, seq_path=root_seq_path, level=0)
    index: dict[str, CreoEntity] = {root.seq_path: root}

    def _build_from_node(node: dict[str, Any], parent_level: int) -> CreoEntity:
        file_name = _get_file_name(node) or ""
        seq_path = _get_seq_path(node)
        if not seq_path:
            seq_path = f"{root.seq_path}.unknown_{len(index)}"
            _logger.warning("BOM node missing seq_path; generated fallback: %s", seq_path)

        level = node.get("level")
        if not isinstance(level, int):
            if "." in seq_path:
                level = seq_path.count(".")
            else:
                level = parent_level + 1

        transform = node.get("transform") if "transform" in node else None
        if get_transforms and transform is None:
            _logger.warning("Missing transform data for node %s", seq_path)
        entity = CreoEntity(
            file_name=file_name,
            seq_path=seq_path,
            level=level,
            transform_matrix=transform if get_transforms else None,
        )
        index[seq_path] = entity

        for child_node in _iter_child_nodes(node):
            child_entity = _build_from_node(child_node, entity.level)
            entity.add_child(child_entity)
        return entity

    if root_node:
        children = _iter_child_nodes(root_node)
        if not children:
            _logger.warning("Root node has no children: %s", root_seq_path)
        for child_node in children:
            child_entity = _build_from_node(child_node, root.level)
            root.add_child(child_entity)
    else:
        children = _iter_child_nodes(bom_res)
        if not children:
            _logger.warning("BOM response has no children")
        for child_node in children:
            child_entity = _build_from_node(child_node, root.level)
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

    if not isinstance(bom_res, dict):
        raise RuntimeError(f"Unexpected BOM response type: {type(bom_res)}")

    bom = _build_entity_tree(bom_res, get_transforms=get_transforms)

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
    def _bbox_value(bbox: dict[str, Any], *keys: str) -> float:
        for key in keys:
            if key in bbox and bbox[key] is not None:
                return float(bbox[key])
        return 0.0

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
                    _logger.warning(
                        "Creoson API error for parameters '%s': %r",
                        file_name,
                        exc,
                        exc_info=True,
                    )
                    parameter_cache[file_name] = []
            entity.parameters = list(parameter_cache[file_name])

        if include_mass_props:
            if file_name not in mass_cache:
                try:
                    mass_cache[file_name] = client.file_massprops(file_=file_name) or {}
                except Exception as exc:
                    _logger.warning(
                        "Creoson API error for mass properties '%s': %r",
                        file_name,
                        exc,
                        exc_info=True,
                    )
                    mass_cache[file_name] = {}
            mass_props = mass_cache[file_name]
            entity.mass = float(mass_props.get("mass") or 0.0)
            entity.volume = float(mass_props.get("volume") or 0.0)

        if include_bounding_box:
            if file_name not in bbox_cache:
                try:
                    bbox_cache[file_name] = client.geometry_bound_box(file_=file_name) or {}
                except Exception as exc:
                    _logger.warning(
                        "Creoson API error for bounding box '%s': %r",
                        file_name,
                        exc,
                        exc_info=True,
                    )
                    bbox_cache[file_name] = {}
            bbox = bbox_cache[file_name]
            try:
                max_x = _bbox_value(bbox, "max_x", "xmax")
                min_x = _bbox_value(bbox, "min_x", "xmin")
                max_y = _bbox_value(bbox, "max_y", "ymax")
                min_y = _bbox_value(bbox, "min_y", "ymin")
                max_z = _bbox_value(bbox, "max_z", "zmax")
                min_z = _bbox_value(bbox, "min_z", "zmin")
                entity.length = max_x - min_x
                entity.width = max_y - min_y
                entity.height = max_z - min_z
            except Exception:
                _logger.warning("Invalid bounding box data for '%s': %s", file_name, bbox)


def get_assembly_component_files(client: creopyson.Client, target_model: str) -> set[str]:
    """
    Return only unique component file names from an assembly (minimal mode).
    """
    return get_assembly_component_file_names(
        client,
        target_model,
        include_root=False,
    )


def get_assembly_component_file_names(
        client: creopyson.Client,
        target_model: str,
        *,
        include_root: bool = False,
) -> set[str]:
    """
    Return unique component file names from an assembly.
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
    if include_root:
        return {entity.file_name for entity in bom.index.values() if entity.file_name}
    return {
        entity.file_name
        for entity in bom.index.values()
        if entity.file_name and entity is not bom.root
    }
