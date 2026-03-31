# BOM Export

**Path:** `src/aas_creo_bridge/adapters/creo/bom_export.py`

## Overview

The BOM export module fetches assembly structure data from Creo via Creoson and
maps it into a structured in-memory tree. The main entry point,
`get_assembly_data`, returns a `CreoBom` with a root node and an index by
`seq_path`. Optional flags allow enrichment with parameters, mass properties,
bounding boxes, and transform matrices.

Two helper functions return the unique component file names of an assembly for
lightweight workflows.

## Key Concepts

### Seq Path

Each BOM entity is identified by a `seq_path` (for example `root.1.2`). This
path is used to build the hierarchy and to index nodes for fast lookup.

### Root Resolution

Creoson can return the root node either as `children` (a dict) or as the BOM
object itself. The adapter normalizes both shapes and logs when data is
unexpected.

### Optional Enrichment

`include_parameters`, `include_mass_props`, and `include_bounding_box` trigger
additional Creoson API calls per file. Results are cached per file name to avoid
repeated calls when the same component appears multiple times.

## Main Components

### `get_assembly_data(...) -> CreoBom`

Fetches the BOM from Creoson, builds a tree of `CreoEntity` nodes, and optionally
enriches each node.

Key parameters:

- `client`: Connected `creopyson.Client`.
- `file_`: Target assembly file name. If `None`, Creo uses the active model.
- `get_transforms`: If `True`, include `transform_matrix` on each node.
- `include_parameters`, `include_mass_props`, `include_bounding_box`: Enable
  enrichment from Creoson API calls.

Returns a `CreoBom` with `root` and `index`.

### `get_assembly_component_files(client, target_model) -> set[str]`

Returns unique component file names for the given assembly. This is a thin
wrapper around `get_assembly_component_file_names` with `include_root=False`.

### `get_assembly_component_file_names(client, target_model, include_root=False) -> set[str]`

Returns unique component file names. When `include_root=True`, the root assembly
file is included.

## Error Handling

| Scenario                           | Behavior                              |
|------------------------------------|---------------------------------------|
| BOM request fails                  | Raises `RuntimeError`                 |
| BOM response is not a dict         | Raises `RuntimeError`                 |
| Parameter/mass/bbox API call fails | Logs warning, uses empty defaults     |
| Missing `seq_path` or `transform`  | Logs warning, generates fallback path |

## Testing

Integration tests are in
[`tests/creo_adapter/test_bom_export.py`](../../../../tests/creo_adapter/test_bom_export.py).

Run:

```bash
pytest tests/creo_adapter/test_bom_export.py -v
```

## Common Patterns and Gotchas

### 1) `file_` is optional

When `file_` is `None`, Creo uses the active model. This can be convenient in
interactive sessions but is less deterministic in automated runs.

### 2) Transforms are only present when requested

If `get_transforms=False`, `transform_matrix` will be `None` for all entities.

### 3) Cache is per file name

If the same component appears multiple times, enrichment results are reused.

## Related Documentation

- [`docs/Modules/aas_creo_bridge/creo_adapter/types.md`](./types.md)
- [`docs/Modules/aas_creo_bridge/creo_adapter/creo_connection.md`](./creo_connection.md)
- [`docs/Modules/aas_creo_bridge/creo_adapter/model_import.md`](./model_import.md)
