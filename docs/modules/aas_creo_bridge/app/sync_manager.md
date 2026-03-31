# Synchronization Manager

**Path:** `src/aas_creo_bridge/app/sync_manager.py`

## Overview

The `SynchronizationManager` coordinates the mapping and tracking of synchronizations between Asset Administration
Shells (AAS) and Creo models. It handles the extraction and import of 3D models from the AASX packages into Creo
Parametric and manages the bidirectional references (links) between AAS Shell IDs and Creo Model Names.

The manager listens for changes in the `AASXRegistry` to automatically establish links or remove them when packages are
registered or unregistered.

## Key Concepts

### Connections and Links

Connections are represented by the `ConnectionLink` dataclass, which maps an `aas_shell_id` to a `creo_model_name`.
Linking is strictly 1:1. The manager tracks these links in two separate dictionaries:

- `_links_by_aas_id`: Lookups by AAS Shell ID.
- `_links_by_creo_model`: Lookups by Creo Model Name (names are automatically normalized to lowercase).

Setting or querying a link ensures consistency across both mapping indexes.

### Model Synchronization

The core behavior of the `SynchronizationManager` is moving data from an AAS package to the Creo session. The
`sync_aas_to_creo()` method orchestrates:

1. Fetching the AAS shell details via the registry.
2. Selecting the best suitable 3D model utilizing consuming applications mappings.
3. Materializing the payload file to a temporary directory.
4. Sending the file to the active Creo session using the `CreosonClient`.
5. Annotating the newly created or updated Creo part with crucial AAS properties (`AAS_ID` and `GLOBAL_ASSET_ID`) as
   model parameters.

## Main Components

### `ConnectionLink`

A dataclass representing the linkage between an AAS identifier and a Creo model name.

- `aas_shell_id: str | None`
- `creo_model_name: str | None`

### `SynchronizationManager`

The primary class that maintains the synchronization mappings and logic.

#### Key Initialization

- `__init__()`: Sets up default applications (e.g., Creo 12 and STEP AP242) for format preference, creates a temporary
  directory for payload extraction, and connects to the AASX registry changes via a listener callback.

#### Link Management

- `link(aas_shell_id, creo_model_name)`: Establishes a mapping. Raises a `RuntimeError` if an ID or model is already
  mapped to a different counterpart.
- `unlink(key)`: Breaks a linkage, looking up by either AAS ID or Creo model name.
- `unlink_all()`: Clears all mapping relationships.
- `list_links()`: Returns a list of all current `ConnectionLink`s.
- `get_link_by_aas_id(aas_shell_id)`: Fetches the linkage via an AAS ID.
- `get_link_by_creo_model(creo_model_name)`: Fetches the linkage via a Creo model name (case-insensitive).

#### Sync Operations

- `sync_aas_to_creo(aas_id: str)`: Executes the full payload extraction and import pipeline. It will log errors and
  warnings if it encounters issues during model extraction, Creo importing, or when setting part parameters.

#### Event Hooks

- `_on_registry_changed(action, shells)`: Bound to the registry's events. When an AAS package is added or removed, it
  invokes `link` (with no Creo model name yet) or `unlink` respectively.

## Usage Example

```python
from aas_creo_bridge.app.context import get_sync_manager

sync_manager = get_sync_manager()

# Initiate synchronization for a specific AAS Shell
# This extracts the file, imports it to Creo, and writes parameters on the part
sync_manager.sync_aas_to_creo("https://example.com/ids/aas/1234")

# Look up the created link
link = sync_manager.get_link_by_aas_id("https://example.com/ids/aas/1234")
if link:
    print(f"AAS Shell is linked to Creo Model: {link.creo_model_name}")
```

## Error Handling

| Scenario                                      | Behavior                                                                                                 |
|-----------------------------------------------|----------------------------------------------------------------------------------------------------------|
| Linking to already mapped component           | Raises `RuntimeError` describing the mapping conflict                                                    |
| Model not found in AAS via `sync_aas_to_creo` | Leaves Creo state unchanged, logs an error/warning and returns `None`                                    |
| Creoson client not available                  | Fails gracefully and logs an error, aborting the process                                                 |
| Failure setting Creo part parameters          | Discarded as an exception; the error is logged, but the model import itself isn't completely rolled back |

## Integration Points

- **Context (`context.py`)**: Uses the context module to fetch the global instance of `AASXRegistry` and the global
  `CreosonClient`.
- **Adapters (`import_model_into_creo`, `set_part_parameters`)**: Sub-modules mapped to handle actual connection
  translation against Creo.
- **AAS Adapter**: Sources models, formats, and materializes local copies from `aas_adapter`.

## Common Patterns and Gotchas

### 1) Normalization

Creo models are normalized to lower-case inside the link directories to prevent casing anomalies from the CAD engine
breaking map searches.

### 2) Temporary Directory

Payloads are extracted to a temporary directory created at class instantiation. This lifecycle matches the run period of
`SynchronizationManager`. The temporary elements might persist if the app abruptly terminates.

