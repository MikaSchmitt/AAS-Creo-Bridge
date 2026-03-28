okay# Types Documentation

## Intent

Defines data classes used by the Creo adapter to represent a hierarchical BOM in memory.
The structure mirrors the IDTA Hierarchical Structures enabling Bills of Material model:
an EntryNode (root) with Node children connected by HasPart relations.

## IDTA Context

- **EntryNode (IDTA)**: Base entry point of the entity tree. Mapped to `CreoBom.root`.
- **Node (IDTA)**: Hierarchical nodes under the entry point. Mapped to `CreoEntity` instances.
- **HasPart / IsPartOf (IDTA)**: Parent–child relations. Represented by `CreoEntity.children`.

The fields `seq_path` and `transform_matrix` are used to preserve structural identity
and placement context from Creo BOM output. These are not part of the core IDTA
field set, but provide practical context for traversal and spatial placement.

## Data Classes

- `Parameter`:
    - `name`: Parameter name
    - `type`: Parameter type (string from Creo)
    - `value`: Parameter value

- `PartParameters`:
    - `file_name`: Component file name
    - `parameters`: List of `Parameter`

- `CreoEntity`:
    - `file_name`: Creo model file name
    - `seq_path`: Unique hierarchical path (e.g. `root.1.2`)
    - `level`: Depth in the hierarchy
    - `parameters`: Optional list of `Parameter`
    - `mass`, `volume`: Optional physical properties
    - `length`, `width`, `height`: Optional bounding box extents
    - `transform_matrix`: Optional placement matrix from BOM export
    - `children`: Child entities (HasPart)

- `CreoBom`:
    - `root`: Root `CreoEntity` (EntryNode)
    - `index`: Lookup by `seq_path` for fast access

## Behavior

- `CreoEntity.add_child` appends a child to the hierarchy.
- `CreoEntity.find_by_path` recursively searches by `seq_path`.
- `CreoBom.get` returns a node by `seq_path` from the index.

## Notes

The IDTA documents define the hierarchical structure conceptually through
EntryNode/Node and HasPart/IsPartOf relations. The adapter stores additional
technical fields (parameters, transforms, physical properties) to support
Creo-specific workflows while keeping the core hierarchy IDTA‑compatible.
