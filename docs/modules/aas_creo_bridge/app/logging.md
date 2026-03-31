# Logging

**Path:** `src/aas_creo_bridge/app/logging.py`

## Overview

The `logging` module provides a comprehensive system for capturing, formatting, and storing log messages across the
application and its dependencies. It intercepts standard Python `logging` emissions and redirects them into an
in-memory `LogStore`, which serves as the central hub for the application's logging state.

This system guarantees that developers and users gain direct access to diagnostic events—enabling live log streaming to
GUI components.

## Key Concepts

### Standard Logging Integration (`AppLogHandler`)

The `AppLogHandler` bridges Python's built-in `logging.Handler` to the app's internal log tracking mechanism.
It listens for any Python-generated log records, normalizes their metadata (e.g., extracting tracebacks and mapping
`logging` severity levels to internal `LogLevel` enums), and writes them seamlessly to the `LogStore`.

### In-Memory Tracking (`LogStore`)

The `LogStore` object acts as an ongoing repository mapping all outputted application events. It maintains a list of
`LogEntry` dataclasses.

To expose these logs dynamically, the store uses an Observer pattern. Features that want to report real-time logging
results can attach callable listeners by invoking `log_store.subscribe(listener)`. Each time a new log is processed, all
registered listeners immediately receive the entry context.

## Main Components

### `LogEntry`

A frozen dataclass representing an individual event.

- `timestamp: datetime`: When the event occurred.
- `level: LogLevel`: The mapped severity (e.g., DEBUG, INFO, WARNING, ERROR).
- `message: str`: A formatted message combining the source logger name and native message.
- `exc_info: str | None`: Stack trace string if the event included an exception traceback.
- `format(...) -> str`: Provides a readable formatted string output of the log line.

### `LogStore`

The repository maintaining logging boundaries.

- `entries`: Returns a shallow copy of tracked `LogEntry` records.
- `lines`: Returns string mappings of all stored logs.
- `last_message`: Fetches only the most recently broadcasted log message for displaying in condensed widgets.
- `subscribe(listener)`: Registers a callback to trigger on incoming updates.
- `add(...) -> LogEntry`: Pushes a raw log string and level through the mapping logic into the entries list.
- `clear()`: Purges current in-memory store.

### `setup_logging(log_store: LogStore) -> None`

Bootstraps logging behavior at application startup.

- Configures the custom `AppLogHandler` handler.
- Hooks it into the root logger.
- Explicitly adjusts verbosity rules per package, setting base filtering to `logging.ERROR`, but enabling `DEBUG`
  specifically on critical domains (`aas_creo_bridge`, `aas_adapter`, `basyx`) and `INFO` on `creopyson` to prevent
  overly
  verbose debug outputs.

## Usage Example

```python
import logging
from aas_creo_bridge.app.logging import LogStore, setup_logging

# Create the core store and prep the STD-LIB injection
store = LogStore()
setup_logging(store)


# Optionally: Track live updates
def on_new_log(entry):
    print(f"I saw a real-time event: {entry.message}")


store.subscribe(on_new_log)

# Later anywhere in the application
logger = logging.getLogger("aas_creo_bridge.my_component")
logger.info("This is an info payload.")

# And if we want the current state manually
lines = store.lines
print("All log strings:", lines)
```

## Integration Points

- **`context.py`**: Exports the global `init_log_store()` logic keeping the `LogStore` accessible globally over the
  application lifecycle.
- **`main.py`**: Invokes `setup_logging()` using the globally exposed log store during initial bootstrapping.
- **GUI Views (`LogWindow`, `StatusBar`)**: Subscribes to the context's Log store pointer so interfaces visually update
  without forcing a rigid dependency loop.

