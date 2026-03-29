#

## Purpose

The `aas_adapter` is a toolkit for working with AAS. It builds upon the
[basyx-python-sdk](https://github.com/eclipse-basyx/basyx-python-sdk) and extends its functionality with classes and
helper functions for common tasks. The `aas_adapter` is the core of the `aas_adapter` and was designed in conjunction
with the `aas_creo_bridge` and therefore currently focuses on workflows related to CAD.

## Featureset

- **AASX import:** AASX files can be loaded from disk to import AAS into the program.
- **in-memory registry:** A registry for storing and managing imported AAS and their models in memory.
- **model extraction:** Extract models files from Model3D and MCAD submodels.
- **model selection:** Select the best model from a list of models based on a given consuming application and or file
  format.
- **file materialization:** Materialize a model into a file based on a given file format for import into the CAD
  software.

## Public API

**functions:**

- import_aasx,
- AASXRegistry,
- get_models_from_aas,
- select_best_model,
- materialize_model_file

**data classes:**

- ConsumingApplication,
- FileFormat,
- FileMetadata,
- FileData,
- Version

## Workflow

A typical workflow for importing an AASX file could look like this:

1. Import the AASX with `import_aasx()`
2. Register the AASX `AASXRegistry.register()`
3. Get the models from the AAS with `get_models_from_aas()`
4. Select a model file based on preferred consuming application and file format with `select_best_model()`
5. Write the selected model file to disk with `materialize_model_file()`

## Minimal usage example

The following example demonstrates extracting a model file from an AASX file and materializing it.

```python
from pathlib import Path
from aas_adapter import (
    import_aasx,
    AASXRegistry,
    get_models_from_aas,
    select_best_model,
    ConsumingApplication,
    FileFormat,
    materialize_model_file,
)

### Importing an AASX file

file_path = Path("example.aasx")
result = import_aasx(file_path)

aasx_registry = AASXRegistry()
aasx_registry.register(result)

### Retrieving AASX from registry
# aasx is technically the same as result in this example,
# but we still go through the registry for demonstration purposes

aas_id = result.shells[0]
aasx = aasx_registry.get_aasx(aas_id)

models = get_models_from_aas(aasx, aas_id)

best_model = select_best_model(
    models,
    [ConsumingApplication("Creo Parametric", "12", "CREO12")],
    [FileFormat("STEP", "AP214", "STEP-214")]
)

output_path = Path("")
prepared_model = materialize_model_file(aasx, best_model, output_path)

```

## Known limitations

`ExternalFile` in `Model3D` is detected but the extraction is not supported yet. Occurrences of `ExternalFile` are
logged.

The file format in `Model3D` and `MCAD` is not standardized in the specification. The `aas_adapter` assumes that the
file format is present as in the file format specification by CADENAS.

## Related Documentation

- [Getting Started](../../docs/guides/setup.md) - How to set up the development environment and run the application.
- [basyx-python-sdk](https://github.com/basyx/basyx-python-sdk) - The core library of the `aas_adapter`.
- [Project architecture](../../docs/architecture/overview.md) - get an overview over the project's architecture
- [AAS-Adapter Importer](../../docs/modules/aas_adapter/importer.md) - How to import AASX files.
- [AAS-Adapter Registry](../../docs/modules/aas_adapter/registry.md) - How to manage the registry of imported AAS.
- [AAS-Adapter Extractor](../../docs/modules/aas_adapter/extractor.md) - How to extract 3D models from imported shells.
- [AAS-Adapter Selection](../../docs/modules/aas_adapter/selection.md) - How to select the best model from a list of
  models.
- [AAS-Adapter Materializer](../../docs/modules/aas_adapter/materializer.md) - How to materialize models into files.
