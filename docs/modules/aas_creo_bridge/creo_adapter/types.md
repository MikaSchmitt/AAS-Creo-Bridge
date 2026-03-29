# Types

**Path:** `src/aas_creo_bridge/adapters/creo/types.py`

## Overview

The types module defines the data structures used by the Creo adapter. It
includes BOM entities and parameters as well as session tracking structures.

## Main Components

### `Parameter`

Represents a single Creo parameter.

Fields:

- `name` (`str`)
- `type` (`str`)
- `value` (`Any`)

### `PartParameters`

Groups a file name with a list of parameters.

Fields:

- `file_name` (`str`)
- `parameters` (`list[Parameter]`)

### `CreoEntity`

Represents a node in the assembly hierarchy.

Fields:

- `file_name` (`str`)
- `seq_path` (`str`)
- `level` (`int`)
- `parameters` (`list[Parameter]`)
- `mass` (`float`)
- `volume` (`float`)
- `length` (`float`)
- `width` (`float`)
- `height` (`float`)
- `transform_matrix` (`Optional[List[float]]`)
- `children` (`list[CreoEntity]`)

Methods:

- `add_child(child)`: Appends a child entity.
- `find_by_path(path)`: Recursively searches by `seq_path`.

### `CreoBom`

Root container for the hierarchy and its index.

Fields:

- `root` (`CreoEntity`)
- `index` (`dict[str, CreoEntity]`)

Method:

- `get(path)`: Returns an entity by `seq_path` from the index.

### `CreoSessionFile`

Immutable representation of a file in the Creo session.

Fields:

- `file_name` (`str`)
- `revision` (`int`)

### `CreoSessionState`

Snapshot of the current Creo session.

Fields:

- `files` (`dict[str, CreoSessionFile]`)
- `active_file_name` (`Optional[str]`)
- `captured_at` (`datetime`, UTC)

### `CreoSessionDelta`

Immutable description of changes between two session states.

Fields:

- `added` (`tuple[CreoSessionFile, ...]`)
- `removed` (`tuple[CreoSessionFile, ...]`)
- `revision_changed` (`tuple[CreoSessionFile, ...]`)
- `active_file_changed` (`bool`)
- `previous_active_file_name` (`Optional[str]`)
- `current_active_file_name` (`Optional[str]`)

Property:

- `has_changes`: `True` if any change is present.

## Related Documentation

- [`docs/Modules/aas_creo_bridge/creo_adapter/bom_export.md`](./bom_export.md)
- [`docs/Modules/aas_creo_bridge/creo_adapter/set_parameter.md`](./set_parameter.md)
