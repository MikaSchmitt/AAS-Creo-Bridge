# Model Import

**Path:** `src/aas_creo_bridge/adapters/creo/model_import.py`

## Overview

The model import module opens native Creo models or imports common exchange
formats into Creo via Creoson. The function detects the format from the file
extension, calls the appropriate Creoson API, and returns the opened Creo model
name.

## Main Components

### `import_model_into_creo(client, path) -> str`

Opens or imports a model into Creo based on file extension.

Parameters:

- `client` (`creopyson.Client`): Connected client.
- `path` (`Path`): Absolute file path to the model.

Returns:

- `str`: The opened model name as returned by Creoson.

## Behavior

- Validates that `path` exists, is absolute, and is a file.
- Native formats (`.asm`, `.prt`) are opened directly with `file_open`.
  The revision suffix (for example `.asm.1`) is stripped before opening.
- Exchange formats are imported via `interface_import_file`:
  - STEP (`.stp`, `.step`)
  - IGES (`.igs`, `.iges`) (not tested)
  - NEUTRAL (`.neu`) (not tested)
  - PV (`.pvz`, `.pvs`) (not tested)
- The imported model is opened and the opened file name is returned.

## Error Handling

| Scenario                              | Behavior                 |
|---------------------------------------|--------------------------|
| Path does not exist                   | Raises `FileNotFoundError` |
| Path is not absolute or not a file    | Raises `ValueError`      |
| Unsupported extension                 | Raises `ValueError`      |
| Creoson import/open failure           | Raises `RuntimeError`    |

## Testing

This function is exercised by integration tests in
[`tests/creo_adapter/test_bom_export.py`](../../../tests/creo_adapter/test_bom_export.py).

## Common Patterns and Gotchas

### 1) Revision suffixes in native files

Native files like `assembly.asm.1` are opened by stripping the trailing
revision suffix. Ensure the file is in Creo's search path.

### 2) Exchange import always creates a Creo model

For exchange formats, Creoson creates a Creo model and returns its name. That
name is then used in `file_open`.

## Related Documentation

- [`docs/Modules/aas_creo_bridge/creo_adapter/creo_connection.md`](./creo_connection.md)
- [`docs/Modules/aas_creo_bridge/creo_adapter/bom_export.md`](./bom_export.md)
