# Creo Connection Documentation

## Intent
`connect_to_creoson` starts the Creoson server from a given folder and establishes a client connection with retry logic.

## Input Values
- `server_folder` (`str | pathlib.Path`): Folder that contains `creoson_run.bat` used to start the Creoson server.
- `max_retries` (`int`, default `5`): Maximum number of connection attempts.
- `delay` (`int`, default `2`): Delay in seconds between retries.

## Return Values
- `creopyson.Client`: A connected Creoson client instance.

## Behavior
- Validates that `creoson_run.bat` exists inside `server_folder`.
- Launches the batch file in a new console window.
- Attempts to connect to Creoson and retries on failure.

## Errors
- `FileNotFoundError`: If `creoson_run.bat` is missing.
- `RuntimeError`: If the server cannot be started or the connection fails after all retries.
