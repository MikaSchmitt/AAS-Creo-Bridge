# Creo Connection

**Path:** `src/aas_creo_bridge/adapters/creo/creo_connection.py`

## Overview

The Creo connection module starts the Creoson server and establishes a client
connection with retry logic. It expects a folder that contains
`creoson_run.bat`, launches the server in a new console, and then connects using
`creopyson.Client`.

## Main Components

### `connect_to_creoson(server_folder, max_retries=5, delay=2) -> creopyson.Client | None`

Starts Creoson and attempts to connect.

Parameters:

- `server_folder` (`str | Path`): Folder containing `creoson_run.bat`.
- `max_retries` (`int`): Number of connection attempts.
- `delay` (`int`): Delay in seconds between attempts.

Returns a connected `creopyson.Client` or raises on failure. The function
currently returns `None` only if the retry loop exits without a connection,
which should not happen in normal flow.

## Behavior

- Validates that `creoson_run.bat` exists before launching.
- Starts the server process with `subprocess.Popen` and `CREATE_NEW_CONSOLE`.
- Retries `client.connect()` until successful or attempts are exhausted.

## Error Handling

| Scenario                                  | Behavior                 |
|-------------------------------------------|--------------------------|
| `creoson_run.bat` missing                 | Raises `FileNotFoundError` |
| Server process fails to launch            | Raises `RuntimeError`    |
| Connection fails after all retries        | Raises `RuntimeError`    |
| Creoson connection error (`MissingKey`)   | Raises `RuntimeError`    |

## Testing

This function requires a running Creo + Creoson setup. It is exercised by the
integration tests in
[`tests/creo_adapter/test_bom_export.py`](../../../tests/creo_adapter/test_bom_export.py).

## Common Patterns and Gotchas

### 1) The server folder must be correct

`server_folder` must point to the directory that contains `creoson_run.bat`.

### 2) Creoson startup can take time

If connection fails intermittently, increase `max_retries` or `delay`.

## Related Documentation

- [`docs/Modules/aas_creo_bridge/creo_adapter/model_import.md`](./model_import.md)
- [`docs/Modules/aas_creo_bridge/creo_adapter/bom_export.md`](./bom_export.md)
