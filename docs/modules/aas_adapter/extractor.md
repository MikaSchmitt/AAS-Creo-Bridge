# Extractor

**Path:** [`src/aas_adapter/extractor.py`](../../../src/aas_adapter/extractor.py)

## Overview

The extractor module is responsible extracting 3D Models in the form of CAD documents and related Information from AAS.
The Extractor requires an AASX import result containing an object store and a file store as well as an AAS identifier.
Given those it first locates `Provision of 3D Models` and `MCAD` submodels. Then it parses the metadata including file
versions, file
formats and consuming applications. It also extracts references to the supplemental files (only `DigitalFile`,
`ExternalFile` is not supported yet). All of this information is then returned as a list of `FileData` objects for
further processing.

## Key Concepts

### Semantic IDs

AAS submodels are identified by their **semantic ID**. Two Submodels are supported:

- **Models3D** (`https://admin-shell.io/idta/Models3D/1/0`): IDTA standard for 3D CAD model metadata.
- **MCAD** (`https://admin-shell.io/sandbox/idta/handover/MCAD/0/1/`): Legacy standard for backwards compatibility.

### Submodel Structure (Models3D)

The following layout shows the submodel structure that the extractor expects for the `Models3D` Submodel. The
specification defines additional submodel elements, however those are currently ignored.

```
Submodel (semantic_id = Models3D)
  ├─ Model3D[] (SubmodelElementList)
      ├─ Model3D[0] (SubmodelElementCollection)
      │   └─ File (SubmodelElementCollection)
      │       ├─ ConsumingApplication[] (SubmodelElementList)
      │       │   ├─ ApplicationName (Property)
      │       │   ├─ ApplicationVersion (Property)
      │       │   └─ ApplicationQualifier (Property)
      │       └─ FileVersion[] (SubmodelElementList)
      │           ├─ FileVersionId (Property)
      │           ├─ FileFormat (SubmodelElementCollection)
      │           │   ├─ FormatName (Property)
      │           │   ├─ FormatVersion (Property)
      │           │   └─ FormatQualifier (Property)
      │           ├─ DigitalFile (File, optional)
      │           └─ ExternalFile (File, optional, not yet supported)
```

When traversing the Submodel all elements are identified and searched for by their `idShort`. Unnecessary elements are
skipped. Consuming Application is treated as optional. The `FileVersion` Submodel Element Collection is essential. If it
is missing a ValueError is raised.

### Submodel Structure (MCAD)

The following layout shows the submodel structure that the extractor expects for the `MCAD` Submodel.
For the `MCAD` submodel there is no documentation as it was never an official submodel and only served as a concept.
Still some AAS providers used the MCAD submodel for distributing 3D model files. As it was the only submodel available
for some time and as of writing the `Provision of 3D Models` submodel is very new the `MCAD` submodel is still widely
used.

The `MCAD` submodel is based on the `Handover Documentation` Submodel however it doesn't have its own documentation.
Therefore, we looked at various AAS from providers using MCAD (mainly FESTO) to reverseengineer its usage. This gave us
the following structure:

```
Submodel (semantic_id = MCAD)
   ├─ Document (SubmodelElementCollection)
   │   ├─ DocumentClassification (SubmodelElementCollection)
   │   │   ├─ ClassIdentifyer (Property)
   │   │   └─ ClassificationSystem (Property)
   │   └─ DocumentVersion (SubmodelElementCollection)
   │       ├─ DocumentVersion (Property)
   │       ├─ DocumentName (MultiLanguageProperty)      
   │       └─ DigitalFile (File)
```

The structure only shows submodel elements that are necessary for the extractor.
It is possible that other providers of ASS have a different interpretation of the MCAD submodel.

To find the CAD documents the extractor takes the following approach.

1. Given an MCAD Submodel the extractor looks for the `Document` submodel element collections in the list of child
   elements.
2. Then the extractor looks for the `DocumentClassification` to check if the document is a CAD document. It checks for
   classification system `VDI2770:2020` and classification identifier `02-02`. Other classification systems and
   identifiers are not supported.
3. Then is looks for the `DocumentVersion` to extract the metadata of the document. It extracts the `DocumentVersion`
   property, the `DocumentName` property, which it expects to be the file format, and the `DigitalFile` property, which
   stores the path to the file and the MIME type.

### File Data Collection

For each File collection, the extractor collects:

1. **Consuming Applications**: What software can open the model. (only Models3D)
2. **Metadata**: Different versions/representations of the same model, each with format and file reference.

### File Format

The file format is expected to follow the
[CADENAS standard](https://cadenas-admin.partcommunity.com/PARTcommunityManagement/FormatList?portal=3dfindit) for file
formats. In the case of `Models3D` it consists of Format Name, Format Version, and Format Qualifier.
For `MCAD` the file format is given as a single string which needs to be parsed into the File Format.
The extractor attempts to parse the file format string into the File Format based on the CADENAS standard.

### Consuming Application

The Consuming Application follows the same format as the File Format: Application Name, Application Version and
Application Qualifier.

## Main Components

### `get_models_from_aas(aasx: AASXImportResult, aas_id: str) -> list[FileData]`

**Purpose:**  
Traverse a given AAS and return a list of all CAD documents with their metadata and consuming applications.

**Parameters:**

- `aasx` (`AASXImportResult`): The import result from `import_aasx()`.
- `aas_id` (`str`): The unique identifier of the AAS shell to extract models from.

**Returns:**  
`list[FileData]` — A list of FileData objects, one per model/document found. Each FileData contains consuming
applications and metadata (version, file path, format).

**Exceptions:**

- `ValueError`: Raised if a model collection contains no usable `FileVersion`.
- `KeyError`: May be raised if submodel references cannot be resolved (logged and skipped gracefully).
- Other exceptions from BaSyx model access are logged and may propagate.

**Usage Example:**

```python
from pathlib import Path
from aas_adapter import import_aasx, get_models_from_aas

result = import_aasx(Path("model.aasx"))
if result.shells:
    models = get_models_from_aas(result, result.shells[0])
    for file_data in models:
        print(f"Consuming apps: 
        {[app.application_name for app in file_data.consuming_applications]}
        "
        )
        for meta in file_data.metadata:
            print(f"  - Version {meta.file_version}: {meta.filepath}")
```

### Consuming Applications Extraction

**Function:** `_extract_consuming_applications(file_collection) -> list[ConsumingApplication]`

Extracts consuming application metadata from a File collection.
If there is no `ConsumingApplication` element or reading fails an empty list is returned.

Each consuming application includes:

- `application_name`: e.g., "Creo Parametric", "STEP"
- `application_version`: e.g., "12", "242"
- `application_qualifier`: e.g., "CREO12", "AP242"

### File Versions Extraction

**Function:** `_extract_file_versions(file_collection) -> list[FileMetadata]`

Extracts all file versions from a File collection.

**Behavior:**

- Returns one `FileMetadata` per readable `FileVersion` entry.
- **DigitalFile is optional**: If missing or unreadable, that version is skipped (logged as exception, not fatal).
- **ExternalFile is detected but not supported**: A warning is logged; the version is still processed if a DigitalFile
  is present.
- If neither DigitalFile nor ExternalFile is present or readable, that version is skipped.

## MCAD Document Extraction

For submodels with MCAD semantic ID, the extractor:

1. Looks for elements with semantic ID `MCAD_DOCUMENT_SEMANTIC_ID`.
2. Validates document classification (VDI2770:2020, class 02-02).
3. Extracts document version, file path, and name.
4. Maps the document name to a `FileFormat` using the Cadenas format database (via `mcad_doc_name_to_cadenas_format`).
5. Logs a warning and skips documents if format mapping fails.

## Related: Helpers

Uses `get_value()` and `check_expected_model()` from `helpers.py` for safe value extraction and type validation.

## Error Handling

As the implementation of the submodels is subject to interpretation the extractor tries to be as graceful as possible
while still being transparent about its behavior. Only if there is a critical error the extractor raises an error all
other issues are logged and the elements skipped. The following table lists how the extractor treats error that might
occur during the extraction process.

| Exception                         | Scenario                                                 | Behavior                                       |
|-----------------------------------|----------------------------------------------------------|------------------------------------------------|
| `ValueError` (No FileVersion)     | A Model3D entry lacks any readable FileVersion.          | Raised immediately; caller must handle.        |
| `ValueError` (Type mismatch)      | A submodel element is not the expected BaSyx type.       | Logged and re-raised with context.             |
| `KeyError` (Unresolved reference) | A submodel reference cannot be resolved in object store. | Skipped; iteration continues to next submodel. |
| Missing `ConsumingApplication`    | File collection has no consuming applications.           | Returns empty list; not an error.              |
| Missing `DigitalFile`             | FileVersion has no digital file reference.               | Version skipped if ExternalFile also absent.   |
| Invalid MCAD document name        | Document name cannot be mapped to FileFormat.            | Logged as warning; document skipped.           |

## Testing

Tests for the extractor are located in [
`tests/aasx_adapter/test_extractor.py`](../../../tests/aasx_adapter/test_extractor.py).

**Key test scenarios:**

- Valid Models3D submodel with multiple files and versions → correct FileData list
- MCAD document extraction → correct FileFormat mapping
- Missing ConsumingApplication → empty application list (no error)
- Missing DigitalFile → version skipped
- No FileVersion found → `ValueError` raised
- Unresolved submodel reference → skipped (logged)

**Run tests:**

```bash
pytest tests/aasx_adapter/test_extractor.py -v
```

## Common Patterns & Gotchas

### 1. **ValueError on No FileVersion**

If a Model3D entry contains no readable file version, `get_models_from_aas()` raises
`ValueError("No FileVersion found")`. Always wrap extraction in a try-catch if you're tolerant of incomplete AAS data:

```python
from aas_adapter import get_models_from_aas

try:
    models = get_models_from_aas(result, shell_id)
except ValueError as e:
    print(f"Incomplete AAS data: {e}")
    models = []
```

### 2. **ExternalFile Is Not Supported**

If a FileVersion contains an `ExternalFile` reference, the extractor logs a warning but continues. External files (
references to URLs, external repositories, etc.) are not downloaded or handled; only DigitalFile entries are
extracted.

### 3. **Consuming Applications List May Be Empty**

If a File collection has no `ConsumingApplication` elements, `file_data.consuming_applications` will be empty.
Downstream selection logic should handle this gracefully (typically by accepting any model without app constraints).

### 4. **MCAD Document Name Mapping Depends on Cadenas Cache**

The `mcad_doc_name_to_cadenas_format()` function relies on fetching the Cadenas format list over HTTP, with a 1-day TTL
cache. If the network is unavailable and the cache is stale or missing, format mapping fails and the document is
skipped.

### 5. **Submodel References May Not Resolve**

If a submodel reference in the AAS points to a non-existent submodel, the reference resolution fails silently (logged as
exception, iteration continues). This is by design to tolerate partially valid AAS data.

### 6. **Semantic ID Comparison**

Semantic ID matching uses object equality (BaSyx `ModelReference`). Ensure your test data uses the exact same semantic
ID objects or construct them consistently.

## Related Documentation

- **Importer**: [`docs/modules/aas_adapter/importer.md`](./importer.md) — How to load AASX files.
- **Selection**: [`docs/modules/aas_adapter/selection.md`](./selection.md) — How to select the best model from extracted
  options.
- **Materializer**: [`docs/modules/aas_adapter/materializer.md`](./materializer.md) — How to extract and write model
  files to disk.
- **AAS Submodel Templates
  **: [Provision of 3D Models](https://github.com/admin-shell-io/submodel-templates/tree/main/published/Provision%20of%203D%20Models/1/0)
