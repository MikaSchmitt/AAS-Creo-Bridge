# BOM Export Documentation

## Intent
`get_assembly_data` fetches a Creo BOM via Creoson and returns a structured `CreoBom` tree of `CreoEntity` nodes.
Helper functions expose unique component file names for assemblies.

## Input Values
- `client` (`creopyson.Client`): Connected Creoson client used to call Creo APIs.
- `file_` (`str | None`, default `None`): Target assembly file name. If omitted, Creo’s active model is used.
- `paths` (`bool`, default `True`): Request component paths in the BOM response.
- `skeletons` (`bool`, default `False`): Include skeleton components.
- `top_level` (`bool`, default `False`): Return only top-level components.
- `get_transforms` (`bool`, default `False`): Request transform matrices for each component.
- `exclude_inactive` (`bool`, default `False`): Exclude inactive/unregenerated components.
- `get_simpreps` (`bool`, default `False`): Request simplified rep data.
- `include_parameters` (`bool`, default `False`): Fetch parameters via `creopyson.parameter_list`.
- `include_mass_props` (`bool`, default `False`): Fetch mass properties via `file_massprops`.
- `include_bounding_box` (`bool`, default `False`): Fetch bounding box via `geometry_bound_box`.

Helper functions:
- `get_assembly_component_files(client, target_model)` returns unique component file names.
- `get_assembly_component_file_names(client, target_model, include_root=False)` returns unique component file names and can optionally include the root assembly.

## Return Values
- `CreoBom`: Rooted tree of `CreoEntity` nodes with an index by `seq_path`.

## Behavior
- Normalizes BOM responses where `children` can be a dict (root node) or a list.
- Builds an EntryNode (root) and Node children consistent with IDTA hierarchical structures.
- Populates `transform_matrix` only when `get_transforms=True`.
- Populates parameters, mass/volume, and bounding box dimensions only if the corresponding include flags are enabled.
- Caches parameter/mass/bbox lookups per file name for performance.

## Errors
- `RuntimeError`: If the BOM request fails or the response has an unexpected type.
- `RuntimeError`: If Creoson parameter/mass/bbox calls fail.
