# Context

**Path:** `src/aas_creo_bridge/app/context.py`

## Overview

The `context` module acts as a centralized dependency injection container and service locator for the application. It
provides global singleton access to core services and state managers required throughout the application lifecycle.

By centralizing the initialization and retrieval of these components, the module ensures that different parts of the
application (such as the GUI, adapters, and synchronization logic) interact with the same instances of these services.

## Key Concepts

### Singleton Pattern

The module maintains global variables for each core service (e.g., `_log_store`, `_aasx_registry`). These are
initialized lazily upon their first request via getter functions. Subsequent calls return the already initialized
instance.

### Lazy Initialization

To prevent circular imports and reduce startup time, components are imported and initialized only when they are first
requested by their respective `init_*()` or `get_*()` functions.

## Main Components

### Log Store

- `init_log_store() -> LogStore`
- `get_log_store() -> LogStore`

Manages the application's logging history and state via the `LogStore` class.

### Logger

- `get_logger(name: str | None = None) -> logging.Logger`

Returns a standard Python `logging.Logger` instance. The logger is automatically prefixed with `"aas_creo_bridge"` to
maintain a consistent logging hierarchy (e.g., `"aas_creo_bridge.my_module"`).

### AASX Registry

- `init_aasx_registry() -> AASXRegistry`
- `get_aasx_registry() -> AASXRegistry`

Provides access to the `AASXRegistry`, which keeps track of all imported AASX files and their associated digital twins
during the session.

### Synchronization Manager

- `init_sync_manager() -> SynchronizationManager`
- `get_sync_manager() -> SynchronizationManager`

Provides access to the `SynchronizationManager`, which coordinates the bidirectional data synchronization between AASX
models and Creo.

### Creoson Client

- `set_path_to_creoson(path: Path) -> None`: Stores the executable path for the Creoson server.
- `get_creoson_client() -> Client | None`: Retrieves the `creopyson.Client` instance.

If a client already exists, it verifies the connection by calling `connect()`. If the connection fails or no client
exists, it attempts to initialize a new connection using the stored path to the Creoson server via
`connect_to_creoson()`.

### Creo Session Tracker

- `init_creo_session_tracker() -> None`
- `get_creo_session_tracker() -> CreoSessionTracker`

Initializes and manages the `CreoSessionTracker`, which monitors the state of the active Creo Parametric session. It
relies on the Creoson client being available; if the client cannot be initialized, it raises a `RuntimeError`. The
tracker is configured with a polling interval to regularly refresh session data.

## Usage Example

```python
from aas_creo_bridge.app.context import (
    get_logger,
    get_aasx_registry,
    get_sync_manager,
    set_path_to_creoson,
    get_creoson_client
)
from pathlib import Path

# Setup Creoson path
set_path_to_creoson(Path("C:/creoson/creoson_run.bat"))

# Get the logger
logger = get_logger(__name__)
logger.info("Starting up...")

# Retrieve global instances
registry = get_aasx_registry()
sync_manager = get_sync_manager()
client = get_creoson_client()

if client:
    logger.info("Connected to Creoson successfully.")
else:
    logger.error("Failed to connect to Creoson.")
```

## Integration Points

Typical flow in the app:

1. Application startup sets the Creoson path using `set_path_to_creoson()`.
2. UI components access the global `AASXRegistry` to display imported models.
3. Sync logic uses `get_sync_manager()` to execute data mapping rules.
4. Background tasks or connection status indicators use `get_creo_session_tracker()`.

## Error Handling

- **Creoson Client Connection:** `get_creoson_client()` catches `RuntimeError`, `ConnectionError`, and `MissingKey`
  exceptions. If the existing client fails to connect, it resets to `None` and attempts to reconnect.
- **Session Tracker Initialization:** `init_creo_session_tracker()` checks if the Creoson client is available. If it
  returns `None`, it logs an error and raises a `RuntimeError`.

## Common Patterns and Gotchas

### 1) Global State

The module stores state in global variables. This is generally suitable for the application's desktop GUI lifecycle but
can cause issues during unit testing if state is not reset between tests.

### 2) Order of Initialization

`init_creo_session_tracker()` depends on `get_creoson_client()`, which in turn may depend on `set_path_to_creoson()`.
Ensure the path is set early in the application startup.

