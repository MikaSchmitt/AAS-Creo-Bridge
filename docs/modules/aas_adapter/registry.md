# Registry

**Path:** `src/aas_adapter/registry.py`

## Overview

The registry module is responsible for keeping imported AASX files available during one app session.

It requires `AASXImportResult` objects from the importer. Given such a result, it stores it in two indexes:

- by file path (`_by_path`)
- by AAS shell ID (`_by_id`)

This allows UI and sync logic to either resolve by source file or directly by shell ID.

The registry also supports listeners. A listener is just a callback without arguments that is called whenever the
registry changes.

## Key Concepts

### Dual Indexing

The registry maintains two independent lookup indexes:

- **By Path** (`_by_path`): Maps file paths to AASXEntry objects. Use this when you know which AASX file was imported.
- **By Shell ID** (`_by_id`): Maps AAS shell identifiers to AASXEntry objects. Use this when you know which shell you're
  interested in (e.g., from the UI).

This dual structure allows flexible queries without re-searching the entire registry.

The path index is stable per file. The ID index is convenient for shell-driven workflows.

### Listener Pattern

The registry follows a publish-subscribe pattern. Listeners can register callbacks to be notified when:

- A package is registered (added to the registry)
- A package is unregistered (removed from the registry)
- The entire registry is cleared

This decouples the registry from specific UI or business logic components.

### Listeners

Listeners are stored in `_listeners` and called by `_notify_listeners()`. Current signature is:

```python
Callable[[], None]
```

So listeners do not receive action names or payloads. They only get a "registry changed" event.

## Main Components

### `AASXRegistry.__init__()`

Creates empty path index, ID index, and listener list.

### `register(result: AASXImportResult) -> None`

Adds one import result to both indexes and notifies listeners.

Flow:

1. Store result in `_by_path[result.path]`.
2. For each shell in `result.shells`, write `_by_id[shell_id]`.
3. Call `_notify_listeners()`.

If shell IDs already exist, the new value overwrites the old one in `_by_id`.

### `unregister(path: Path) -> None`

Removes an entry from `_by_path` and notifies listeners if the path existed.

Important current behavior: it does **not** remove related entries from `_by_id`.
This can leave stale ID mappings after unregistering by path.

### `get(key: Path | str) -> AASXImportResult | None`

Returns a result by path (`Path`) or shell ID (`str`).

### `is_open(key: Path | str) -> bool`

Checks if a given path or shell ID is currently present in the corresponding index.

### `list_by_path_open() -> list[AASXImportResult]`

Returns all results reachable through the path index.

### `list_by_id_open() -> list[AASXImportResult]`

Returns all results reachable through the ID index.

### `list_clear() -> None`

Clears both indexes and notifies listeners.

### `add_listener(listener: Callable[[], None]) -> None`

Registers a callback.

### `remove_listener(listener: Callable[[], None]) -> None`

Removes a callback if it exists.

## Usage Example

```python
from pathlib import Path

from aas_adapter import AASXRegistry, import_aasx

registry = AASXRegistry()


def on_registry_change() -> None:
    print("Registry changed")


registry.add_listener(on_registry_change)

result = import_aasx(Path("model.aasx"))
registry.register(result)

by_path = registry.get(result.path)
by_id = registry.get(result.shells[0]) if result.shells else None
```

## Integration Points

Typical flow in the app:

1. Import package via `import_aasx()`.
2. Register result via `AASXRegistry.register(...)`.
3. UI reads open packages from `list_by_path_open()`.
4. Sync logic resolves selected shell IDs using `get(shell_id)`.

## Error Handling

| Scenario                         | Behavior                                   |
|----------------------------------|--------------------------------------------|
| `unregister()` with unknown path | No-op, no exception                        |
| `get()` with unknown key         | Returns `None`                             |
| listener callback raises         | Error is logged, other listeners still run |

## Testing

The file `tests/aasx_adapter/test_registry.py` currently exists but has no active test cases.

If you extend registry behavior, recommended test cases are:

- register/get by path and by shell ID
- duplicate shell ID overwrite behavior
- unregister path behavior and current `_by_id` side effect
- listener invocation and listener exception handling
- clear behavior for both indexes

## Common Patterns and Gotchas

### 1) Duplicate shell IDs overwrite old entries in `_by_id`

This is expected with current implementation and marked as a TODO in code.

### 2) `unregister(path)` only updates `_by_path`

After unregistering, ID lookups can still resolve stale entries.

### 3) Listener callback takes no arguments

If code expects action/payload arguments, it will fail at runtime.

### 4) Listener removal requires the same callable object

Use a named function if you need to remove it later.

### 5) Registry is in-memory only

No persistence is implemented. Closing the app loses state.

## Related Documentation

- [`Importer`](./importer.md) — How to create `AASXImportResult` objects.
- [`Extractor`](./extractor.md) — How to extract models from registered packages.
- [`Selection`](./selection.md) — Model selection from extracted results.

