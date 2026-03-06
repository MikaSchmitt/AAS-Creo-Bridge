"""
AASX adapter package.

This package contains the "AASX side" of the bridge: importing AASX packages,
keeping them available during an app session, and extracting model/file
information from AAS Submodels.

Key building blocks
-------------------
- :func:`aas_creo_bridge.adapters.aasx.aasx_importer.import_aasx`:
  Reads an AASX file into a BaSyx object store + supplementary file store.
- :class:`aas_creo_bridge.adapters.aasx.aasx_registry.AASXRegistry`:
  Session registry for opened AASX packages, indexed by path and AAS shell id.
- :func:`aas_creo_bridge.adapters.aasx.get_models.get_models_from_aas`:
  Extracts 3D model file information (consuming applications + file versions)
  from a given AAS within an imported AASX package.
- :func:`aas_creo_bridge.adapters.aasx.helpers.get_value`:
  Small convenience helper to read values from BaSyx SubmodelElements and
  nested elements.

Public API re-exports
---------------------
Importing from :mod:`aas_creo_bridge.adapters.aasx` is supported for the common
entry points (stable convenience surface), e.g.::

    from aas_creo_bridge.adapters.aasx import import_aasx, AASXRegistry, get_models_from_aas

Data structures
---------------
See :mod:`aas_creo_bridge.adapters.aasx.types` for:
- :class:`~aas_creo_bridge.adapters.aasx.types.ConsumingApplication`
- :class:`~aas_creo_bridge.adapters.aasx.types.FileFormat`
- :class:`~aas_creo_bridge.adapters.aasx.types.FileMetadata`
- :class:`~aas_creo_bridge.adapters.aasx.types.FileData`
"""

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult, import_aasx
from aas_creo_bridge.adapters.aasx.aasx_registry import AASXRegistry
from aas_creo_bridge.adapters.aasx.get_models import (
    find_model_for_app,
    get_models_from_aas,
)
from aas_creo_bridge.adapters.aasx.helpers import Version, get_value
from aas_creo_bridge.adapters.aasx.types import (
    ConsumingApplication,
    FileData,
    FileFormat,
    FileMetadata,
)

__all__ = [
    "AASXImportResult",
    "AASXRegistry",
    "ConsumingApplication",
    "FileData",
    "FileFormat",
    "FileMetadata",
    "Version",
    "get_models_from_aas",
    "find_model_for_app",
    "get_value",
    "import_aasx",
]
