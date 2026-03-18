# Model Import Documentation

## Intent
`import_model_into_creo` imports or opens a model in Creo based on the file extension. It supports native Creo files and common exchange formats.

## Input Values
- `client` (`creopyson.Client`): Connected Creoson client used to call Creo APIs.
- `path` (`pathlib.Path`): Path to the file to open or import.
- `use_workdir` (`bool`, default `False`): If `True`, the Creo working directory is set to `path.parent` before importing. If `False`, the directory is passed explicitly to the import/open calls.

## Return Values
- `None`: The function performs the import/open operation and returns nothing on success.

## Behavior
- Validates that `path` exists.
- Optionally changes Creo’s working directory.
- For native formats (`*.asm`, `*.prt`), opens the file directly.
- For non-native formats (`*.stp`, `*.step`, `*.igs`, `*.iges`, `*.neu`, `*.pvz`, `*.pvs`), imports via the interface API and opens the resulting Creo model.

## Errors
- `FileNotFoundError`: If the file path does not exist.
- `RuntimeError`: If setting the working directory fails or if the import/open operation fails.
