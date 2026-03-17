"""
AASX adapter package.

This package contains the "AASX side" of the bridge: importing AASX packages,
keeping them available during an app session, and extracting model/file
information from AAS Submodels.

Key building blocks
-------------------
- :func:`aas_adapter.importer.import_aasx`:
  Reads an AASX file into a BaSyx object store + supplementary file store.
- :class:`aas_adapter.registry.AASXRegistry`:
  Session registry for opened AASX packages, indexed by path and AAS shell id.
- :func:`aas_adapter.extractor.get_models_from_aas`:
  Extracts 3D model file information (consuming applications + file versions)
  from a given AAS within an imported AASX package.
- :func:`aas_adapter.helpers.get_value`:
  Small convenience helper to read values from BaSyx SubmodelElements and
  nested elements.

Public API re-exports
---------------------
Importing from :mod:`aas_adapter` is supported for the common
entry points (stable convenience surface), e.g.::

    from aas_adapter import import_aasx, AASXRegistry, get_models_from_aas

Data structures
---------------
See :mod:`~aas_adapter.models` for:
- :class:`~aas_adapter.models.ConsumingApplication`
- :class:`~aas_adapter.models.FileFormat`
- :class:`~aas_adapter.models.FileMetadata`
- :class:`~aas_adapter.models.FileData`
- :class:`~aas_adapter.models.Version`
"""

from aas_adapter.extractor import get_global_asset_id, get_models_from_aas
from aas_adapter.helpers import get_value
from aas_adapter.importer import AASXImportResult, import_aasx
from aas_adapter.materializer import materialize_model_file
from aas_adapter.models import (
    ConsumingApplication,
    FileData,
    FileFormat,
    FileMetadata,
    Version,
)
from aas_adapter.registry import AASXRegistry, RegistryAction
from aas_adapter.selection import (
    find_model_for_app,
    group_models_by_version,
    filter_model_by_app,
    select_best_model,
)

__version__ = "0.1.1"

__all__ = [
    "AASXImportResult",
    "AASXRegistry",
    "RegistryAction",
    "ConsumingApplication",
    "FileData",
    "FileFormat",
    "FileMetadata",
    "Version",
    "get_global_asset_id",
    "get_models_from_aas",
    "find_model_for_app",
    "group_models_by_version",
    "filter_model_by_app",
    "get_value",
    "import_aasx",
    "materialize_model_file",
    "select_best_model",
]
