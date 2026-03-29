# Set Parameter Documentation

## Intent

`set_parameter` and `set_part_parameters` are thin wrappers around Creoson’s parameter set API.
They are used to write AAS-derived values (e.g., asset IDs) into Creo model parameters.

## Input Values

- `client` (`creopyson.Client`): Connected Creoson client used to call Creo APIs.
- `file_name` (`str`): Target Creo model file name.
- `parameter` (`Parameter`): Single parameter to set.
- `part` (`PartParameters`): File name plus a list of parameters.
- `designate` (`bool | None`, default `True`): Whether the parameter should be designated.
- `no_create` (`bool | None`, default `None`): If `True`, do not create missing parameters.

## Return Values

- `None`: The functions perform the update and return nothing on success.

## Behavior

- `set_parameter` sets exactly one parameter on the given model.
- `set_part_parameters` iterates the parameter list of a `PartParameters` instance and calls `set_parameter` for each
  item.

## Errors

- `ValueError`: If `file_name` or parameter data is missing.
- `RuntimeError`: If Creoson rejects the parameter update.
