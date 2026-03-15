from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, List


@dataclass
class Parameter:
    name: str
    type: str
    value: Any


@dataclass
class CreoEntity:
    # Identification and origin
    file_name: str
    seq_path: str  # IDTA: unique path (e.g. "0.1.5")
    level: int  # hierarchy depth

    # Metadata (parameters)
    parameters: List[Parameter] = field(default_factory=list)

    # Physical properties
    mass: float = 0.0
    volume: float = 0.0

    # Geometric extents
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0

    # Spatial placement (IDTA: relationship context)
    transform_matrix: Optional[List[float]] = None

    # Hierarchical structure (IDTA "HasPart" relation)
    children: List[CreoEntity] = field(default_factory=list)

    def add_child(self, child: CreoEntity):
        """Add a child entity to the hierarchy."""
        self.children.append(child)

    def find_by_path(self, path: str) -> Optional[CreoEntity]:
        """Recursively find an entity by its seq_path."""
        if self.seq_path == path:
            return self
        for child in self.children:
            found = child.find_by_path(path)
            if found:
                return found
        return None


@dataclass
class CreoBom:
    # Root of the hierarchy (EntryNode)
    root: CreoEntity
    # Fast lookup for entities by seq_path
    index: dict[str, CreoEntity] = field(default_factory=dict)

    def get(self, path: str) -> Optional[CreoEntity]:
        """Get an entity by seq_path using the index."""
        return self.index.get(path)
