# Main

**Path:** `src/aas_creo_bridge/app/main.py`

## Overview

The `main` module acts as the entry point and primary bootstrapper for the `AAS-Creo-Bridge` application. Its sole
responsibility is configuring the execution environment sequentially, instantiating the core singleton services, and
launching the graphical user interface.

## Key Concepts

### Startup Sequence

The module executes a distinct sequence of initialization steps before starting the user interface loop. This ensures
that when the UI starts rendering, all necessary background services (logging, hardware/software hooks, state
repositories) are fully initialized and ready to consume events.

## Main Components

### `main() -> None`

This single function orchestrates the lifecycle start-up process. It manages the following configuration flow:

1. **Logging Setup:**
    - Invokes `init_log_store()` via the global `context` to create the application's in-memory `LogStore`.
    - Bootstraps standard python routing utilizing custom logic defined in `setup_logging(log_store)`
      (see [`Logging`](./logging.md)).

2. **Core Context Initialization:**
    - `init_aasx_registry()`: Prepares the in-memory repository to hold the AASX imported shells.
    - `init_sync_manager()`: Bootstraps the business logic orchestrator required to map logic between the parsed
      packages and Creo Parametric active sessions.

3. **External Environment Binding:**
    - Re-maps the physical execution path dynamically by configuring `set_path_to_creoson(Path(...))` to locate the
      hardcoded bridge server (`creoson`).
    - `init_creo_session_tracker()`: Readies dynamic background threads to monitor connection states to the Creo host.
    - Instructs the tracker singleton to immediately begin its automated polling execution via
      `get_creo_session_tracker().start_polling()`.

4. **UI Execution Loop:**
    - Instantiates the root Tkinter application canvas using `MainWindow()`.
    - Locks the execution runtime thread directly into the application instance via `window.run()`.

## Usage Example

To launch the `AAS-Creo-Bridge` application normally, you call the execution namespace typically from an external
runner or top-level `__main__` entry:

```python
from aas_creo_bridge.app.main import main

if __name__ == "__main__":
    main()
```

## Integration Points

- Relies heavily on the `context` module (`init_*`) to securely prepare singleton data structures.
- Triggers the initialization of the `MainWindow` GUI module.
- Directly manipulates paths for external vendor application dependencies linking to the `creoson` binary repository.

