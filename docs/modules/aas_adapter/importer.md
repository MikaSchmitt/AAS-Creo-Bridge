# Importer

**Path:** `src/aas_adapter/importer.py`

## Overview

The importer module is the entry point for loading AASX (Asset Administration Shell eXchange) files into the
application. It reads an AASX package (which is a ZIP-based format), extracts and parses its contents using the BaSyx
AAS SDK, and returns a result containing the AAS object store, supplementary files, package metadata, and a
list of discovered Asset Administration Shell (AAS) identifiers.

It requires a `Path` to an existing `.aasx` file.
Given that path, it creates a BaSyx object store and file store, reads package content via `AASXReader`, then collects
metadata, thumbnail, and AAS shell IDs. The result is returned as one immutable `AASXImportResult` object.

In short, this module does four things:

- Validates that the path exists and points to a file.
- Reads AAS objects and supplementary file references from the package.
- Discovers which identifiers are Asset Administration Shells.
- Returns all import data in a single structured object.

## Key Concepts

### AASX Format

An AASX file is a ZIP-compressed archive that conforms to the
[OPC (Open Packaging Convention)](https://en.wikipedia.org/wiki/Open_Packaging_Conventions) standard. It contains:

- XML-serialized AAS model data (objects, submodels, collections, properties)
- Supplementary files (binary model files, images, documents)
- Package-level metadata (author, creation date, description)
- An optional thumbnail image

### Object Store and File Store

- `DictObjectStore` holds parsed AAS identifiables (shells, submodels, etc.).
- `DictSupplementaryFileContainer` tracks supplementary files contained in the package.

### Shell Discovery

`import_aasx()` receives a set of identifiers from `reader.read_into(...)` and then checks each identifier in the object
store. Only objects that are `AssetAdministrationShell` instances are returned in `result.shells`.

## Main Components

### `import_aasx(path: Path) -> AASXImportResult`

Reads an AASX package and returns a snapshot of the imported content.

**Parameter:**

- `path`: Path to the AASX file.

**Returns:**

- `AASXImportResult.path`: Source file path.
- `AASXImportResult.object_store`: Parsed identifiables.
- `AASXImportResult.file_store`: Supplementary file container.
- `AASXImportResult.metadata`: OPC core properties or `None`.
- `AASXImportResult.thumbnail`: Thumbnail bytes or `None`.
- `AASXImportResult.shells`: IDs of discovered AAS shells.

**Exceptions:**

- `FileNotFoundError` when `path` does not exist or is not a file.
- `ValueError` when reading/parsing fails (reader errors are wrapped and logged).

**Usage Example:**

```python
from pathlib import Path

from aas_adapter import import_aasx

result = import_aasx(Path("model.aasx"))

for shell_id in result.shells:
    aas = result.object_store.get_identifiable(shell_id)
    print(f"Found shell: {aas.id}")

if result.metadata:
    print(f"Creator: {result.metadata.creator}")
```

### `AASXImportResult` (frozen dataclass)

`AASXImportResult` is immutable after creation. This helps avoid accidental changes after registration in
`AASXRegistry`.

Fields:

- `path: Path`
- `object_store: DictObjectStore`
- `file_store: DictSupplementaryFileContainer`
- `metadata: OPCCoreProperties | None`
- `thumbnail: bytes | None`
- `shells: list[str]`

## Integration Points

### Registry

Usually, import is followed by registration:

```python
from pathlib import Path

from aas_adapter import AASXRegistry, import_aasx

registry = AASXRegistry()
result = import_aasx(Path("model.aasx"))
registry.register(result)
```

### Extractor

The extractor expects an import result plus a shell ID:

```python
from pathlib import Path

from aas_adapter import get_models_from_aas, import_aasx

result = import_aasx(Path("model.aasx"))
if result.shells:
    models = get_models_from_aas(result, result.shells[0])
```

### Dependencies

- `basyx.aas` for AASX reading and in-memory stores.
- `pyecma376_2` for OPC core properties.

## Error Handling

Current behavior in `import_aasx()`:

| Exception           | When it happens                     | Notes                                |
|---------------------|-------------------------------------|--------------------------------------|
| `FileNotFoundError` | `path` missing or not a file        | Raised before opening reader         |
| `ValueError`        | Any exception while reading/parsing | Original error is logged and chained |

The module logs failed imports with file path and traceback before raising `ValueError`.

## Testing

Tests are in `tests/aasx_adapter/test_importer.py`.

Covered scenarios include:

- Missing file path and directory path (`FileNotFoundError`).
- Successful import wiring (stores, metadata, thumbnail, shell discovery integration).
- Reader exceptions wrapped as `ValueError` and logged.
- `_discover_shells()` behavior (empty input and filtering by shell type).

Run tests:

```bash
pytest tests/aasx_adapter/test_importer.py -v
```

## Common Patterns and Gotchas

### 1) `shells` can be empty

Not every AASX contains `AssetAdministrationShell` objects.

### 2) `metadata` and `thumbnail` can be `None`

These package fields are optional.

### 3) `file_store` contains references, not eagerly loaded file bytes

Read supplementary files explicitly when needed.

### 4) `AASXImportResult` is frozen, but contained stores are still mutable objects

The dataclass fields cannot be reassigned. The store objects themselves are not deep-copied.

### 5) All reader/parsing errors are surfaced as `ValueError`

If callers need root-cause detail, inspect the chained exception and logs.

## Related Documentation

- [`Extractor`](./extractor.md)
- [`Registry`](./registry.md)
- [BaSyx Python SDK](https://basyx-python-sdk.readthedocs.io/en/latest/index.html)
- [ECMA-376-2 OPC](https://www.ecma-international.org/publications-and-standards/standards/ecma-376/)

