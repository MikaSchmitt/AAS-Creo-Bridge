from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import creopyson

_logger = logging.getLogger(__name__)

def _get_component_data(
    client: creopyson.Client,
    file_name: str,
    *,
    include_parameters: bool,
    include_file_info: bool,
) -> dict[str, Any]:
    """Return optional metadata for one component based on active flags."""
    data: dict[str, Any] = {}
    try:
        if include_parameters:
            data["parameters"] = client.parameter_list(file_=file_name)
        if include_file_info:
            data["info"] = client.file_get_fileinfo(file_=file_name) or {}
        return data
    except Exception as exc:
        _logger.error("Creoson API error for '%s': %r", file_name, exc, exc_info=True)
        raise RuntimeError(f"Creoson API error for '{file_name}'") from exc


def _walk_bom_tree(node: Any, visit_fn) -> None:
    """Traverse BOM tree recursively and call visit_fn for each dict node."""
    if isinstance(node, list):
        for item in node:
            _walk_bom_tree(item, visit_fn)
        return

    if isinstance(node, dict):
        visit_fn(node)
        if "children" in node:
            _walk_bom_tree(node["children"], visit_fn)


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
    include_file_info: bool = False,
    include_enriched_tree: bool = False,
) -> dict[str, Any]:
    """
    Main function: fetch assembly tree and return only the requested data.

    Default behavior is minimal and returns component file names only.
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

    component_files: set[str] = set()

    def _collect_and_optionally_enrich(node: dict[str, Any]) -> None:
        file_name = node.get("file")
        if not file_name:
            return
        component_files.add(file_name)
        if include_parameters or include_file_info:
            node["metadata"] = _get_component_data(
                client,
                file_name,
                include_parameters=include_parameters,
                include_file_info=include_file_info,
            )

    _walk_bom_tree(bom_res, _collect_and_optionally_enrich)
    result: dict[str, Any] = {"component_files": sorted(component_files)}

    if include_enriched_tree:
        result["assembly_tree"] = bom_res
    return result


def get_bom_with_metadata(
    client: creopyson.Client,
    file_: str | None = None,
    *,
    paths: bool = True,
    skeletons: bool = False,
    top_level: bool = False,
    get_transforms: bool = False,
    exclude_inactive: bool = False,
    get_simpreps: bool = False,
) -> dict[str, Any]:
    """Compatibility wrapper: return tree with parameters and file info."""
    result = get_assembly_data(
        client,
        file_=file_,
        paths=paths,
        skeletons=skeletons,
        top_level=top_level,
        get_transforms=get_transforms,
        exclude_inactive=exclude_inactive,
        get_simpreps=get_simpreps,
        include_parameters=True,
        include_file_info=True,
        include_enriched_tree=True,
    )
    return result["assembly_tree"]


def export_bom_with_metadata(
    client: creopyson.Client,
    output_file: Path,
    file_: str | None = None,
    *,
    paths: bool = True,
    skeletons: bool = False,
    top_level: bool = False,
    get_transforms: bool = False,
    exclude_inactive: bool = False,
    get_simpreps: bool = False,
) -> Path:
    """Compatibility wrapper: export tree with full metadata."""
    bom_data = get_assembly_data(
        client,
        file_=file_,
        paths=paths,
        skeletons=skeletons,
        top_level=top_level,
        get_transforms=get_transforms,
        exclude_inactive=exclude_inactive,
        get_simpreps=get_simpreps,
        include_parameters=True,
        include_file_info=True,
        include_enriched_tree=True,
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(bom_data, indent=4), encoding="utf-8")
    return output_file


def get_assembly_component_files(client: creopyson.Client, target_model: str) -> set[str]:
    """
    Return only unique component file names from an assembly (minimal mode).
    """
    result = get_assembly_data(
        client,
        file_=target_model,
        paths=True,
        skeletons=False,
        top_level=False,
        get_transforms=False,
        exclude_inactive=False,
        get_simpreps=False,
        include_parameters=False,
        include_file_info=False,
        include_enriched_tree=False,
    )
    return set(result["component_files"])
