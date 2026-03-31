# Set Parameters

**Path:** `src/aas_creo_bridge/adapters/creo/set_parameter.py`

## Overview

The set parameter module writes parameter values into Creo models via Creoson.
It exposes a single-parameter function and a batch function for a whole part.

## Main Components

### `set_parameter(client, file_name, parameter, designate=True, no_create=None) -> None`

Sets a single parameter on a model.

Parameters:

- `client` (`creopyson.Client`): Connected client.
- `file_name` (`str`): Target Creo file name.
- `parameter` (`Parameter`): Parameter name, type, and value.
- `designate` (`bool | None`): Whether the parameter should be designated.
- `no_create` (`bool | None`): If `True`, do not create missing parameters.

### `set_part_parameters(client, part, designate=True, no_create=None) -> None`

Sets all parameters listed in a `PartParameters` instance by calling
`set_parameter` for each entry.

Parameters:

- `part` (`PartParameters`): Contains the file name and a list of parameters.

## Behavior

- Validates that `file_name` and `parameter.name` are present.
- Logs success and failure with the target file and parameter.
- Batch mode iterates in order and stops on the first failure.

## Error Handling

| Scenario                          | Behavior              |
|-----------------------------------|-----------------------|
| Missing file name                 | Raises `ValueError`   |
| Missing parameter name            | Raises `ValueError`   |
| Empty parameter list (batch mode) | Raises `ValueError`   |
| Creoson update fails              | Raises `RuntimeError` |

## Testing

These functions are covered indirectly by the integration tests in
[`tests/creo_adapter/test_bom_export.py`](../../../../tests/creo_adapter/test_bom_export.py).

## Common Patterns and Gotchas

### 1) Parameter types are passed through

`parameter.type` is sent as-is to Creoson. Use Creo-compatible type strings.

### 2) `no_create=True` prevents new parameters

If the parameter does not exist in the model and `no_create=True`, the update
fails and raises `RuntimeError`.

## Related Documentation

- [`docs/Modules/aas_creo_bridge/creo_adapter/types.md`](./types.md)
