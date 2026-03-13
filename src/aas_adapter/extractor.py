import logging
from typing import Any

from basyx.aas import model
from basyx.aas.model import AssetAdministrationShell

from aas_adapter.helpers import get_value, check_expected_model, mcad_doc_name_to_cadenas_format
from aas_adapter.importer import AASXImportResult
from aas_adapter.models import (
    ConsumingApplication,
    FileData,
    FileFormat,
    FileMetadata,
)

_logger = logging.getLogger(__name__)


def _get_element(obj: Any, prop: str) -> Any:
    """
    Get the value of a property from an object, or its id_short if it's a dict.

    This is an internal helper used while traversing BaSyx model objects.
    Prefer :func:`aas_creo_bridge.adapters.aas_adapter.helpers.get_value` for reading
    SubmodelElement values.

    :param obj: The object to extract the value from.
    :type obj: Any
    :param prop: The property name to use as a fallback.
    :type prop: str
    :return: The extracted value.
    :rtype: Any
    """
    return obj.value.get("id_short", prop)


MODELS3D_SEMANTIC_ID = model.ModelReference(
    (
        model.Key(
            type_=model.KeyTypes.SUBMODEL,
            value="https://admin-shell.io/idta/Models3D/1/0",
        ),
    ),
    type_=model.Submodel,
)

MCAD_SEMANTIC_ID = model.ModelReference(
    (
        model.Key(
            type_=model.KeyTypes.SUBMODEL,
            value="https://admin-shell.io/sandbox/idta/handover/MCAD/0/1/",
        ),
    ),
    type_=model.Submodel,
)

MCAD_DOCUMENT_SEMANTIC_ID = model.ExternalReference(
    (
        model.Key(
            type_=model.KeyTypes.GLOBAL_REFERENCE,
            value="0173-1#02-ABI500#001/0173-1#01-AHF579#001*01",
        ),
    ),
)


def _extract_consuming_applications(
        file_collection: model.SubmodelElementCollection,
) -> list[ConsumingApplication]:
    """
    Extract ``ConsumingApplication`` entries from a ``File`` collection.

    The function is defensive:
    - Missing ``ConsumingApplication`` -> returns an empty list
    - Unexpected errors while reading -> logs and returns an empty list

    Expected structure (idShorts) inside the collection is aligned with the
    IDTA "Models3D" style layout, e.g.::

        File/
          ConsumingApplication/ [ { ApplicationName, ApplicationVersion, ApplicationQualifier }, ... ]

    :param file_collection: The collection of submodel elements to extract from.
    :type file_collection: model.SubmodelElementCollection
    :return: List of consuming applications (empty if not present / unreadable).
    :rtype: list[ConsumingApplication]
    """
    applications: list[ConsumingApplication] = []

    try:
        consuming_apps = file_collection.get_referable("ConsumingApplication")
    except KeyError:
        return applications
    except Exception:
        _logger.exception("Failed to read ConsumingApplication")
        return applications

    values = getattr(consuming_apps, "value", None)
    if not values:
        return applications

    applications = [
        ConsumingApplication(
            get_value(app, "ApplicationName"),
            get_value(app, "ApplicationVersion"),
            get_value(app, "ApplicationQualifier"),
        )
        for app in values
    ]
    return applications


def _extract_file_versions(
        file_collection: model.SubmodelElementCollection,
) -> list[FileMetadata]:
    """
    Extract a ``FileVersion`` entry from a ``File`` collection.

    Notes / current behavior:
    - If multiple ``FileVersion`` items exist, the function currently returns the
      *last* parsed one (this mirrors the current implementation and can be
      extended later to return a list).
    - ``DigitalFile`` is optional; if absent, ``filepath`` and ``file_content_type``
      are returned as empty strings.
    - ``ExternalFile`` is detected and logged, but not supported yet.

    Expected structure (idShorts) inside the collection is typically::

        File/
          FileVersion/ [ { FileVersionId, FileFormat{...}, DigitalFile?, ExternalFile? }, ... ]

    :param file_collection: The collection of submodel elements to extract from.
    :type file_collection: model.SubmodelElementCollection
    :return: Parsed metadata for a file version, or ``None`` if not present/unreadable.
    :rtype: FileMetadata | None
    """
    metadata: list[FileMetadata] = []

    try:
        file_versions = file_collection.get_referable("FileVersion")  # Model3D/[n]/File/FileVersion (SML)
    except KeyError:
        return []  # No SML FileVersion found
    except Exception:
        _logger.exception("Failed to read FileVersion")
        return []

    if not hasattr(file_versions, "value"):
        return []

    file_versions = check_expected_model(file_versions, model.SubmodelElementList)
    for version_item in get_value(file_versions):  # Model3D/[n]/File/FileVersion/[n] (SMC)
        version = get_value(version_item, "FileVersionId")  # Model3D/[n]/File/FileVersion/[n]/FileVersionId (PROP)
        file_format = version_item.get_referable("FileFormat")  # .../FileFormat (SMC)
        format_name = get_value(file_format, "FormatName")  # .../FileFormat/FormatName (PROP)
        format_version = get_value(file_format, "FormatVersion")  # .../FileFormat/FormatVersion (PROP)
        format_qualifier = get_value(file_format, "FormatQualifier")  # .../FileFormat/FormatQualifier (PROP)

        filepath, file_content_type = "", ""
        try:
            digital_file = version_item.get_referable("DigitalFile")  # .../DigitalFile (FILE)
            filepath = digital_file.value
            file_content_type = digital_file.content_type
        except KeyError:
            pass  # DigitalFile is optional
        except Exception:
            _logger.exception("Failed to read DigitalFile")

        try:
            external_file = version_item.get_referable("ExternalFile")  # .../ExternalFile (FILE)
            _logger.warning(
                "AAS contains ExternalFile: %s\nExternal files are not supported yet",
                external_file,
            )
        except KeyError:
            pass  # ExternalFile is optional
        except Exception:
            _logger.exception("Failed to read ExternalFile")

        if not filepath and not file_content_type:
            continue

        metadata.append(FileMetadata(
            version,
            filepath,
            file_content_type,
            FileFormat(format_name, format_version, format_qualifier),
        ))

    return metadata


def get_models_from_aas(aasx: AASXImportResult, aas_id: str) -> list[FileData]:
    """
    Extract 3D models from an Asset Administration Shell within an AASX result.

    The extractor traverses all submodels referenced by the given AAS, and:
    - If a submodel has semantic id :data:`MODELS3D_SEMANTIC_ID`, it looks for the
      ``Model3D`` element list and reads per-item ``File`` collections.
    - For each ``File`` collection it collects:
        * consuming applications via :func:`_extract_consuming_applications`
        * a file version via :func:`_extract_file_versions`

    If no ``FileVersion`` can be extracted for a model, a ``ValueError`` is raised
    (this is treated as a data quality issue for the current workflow).

    :param aasx: The AASX import result containing the object store.
    :type aasx: AASXImportResult
    :param aas_id: The identifier of the AAS to extract models from.
    :type aas_id: str
    :return: A list of FileData objects representing the extracted models.
    :rtype: list[FileData]
    """
    files: list[FileData] = []

    aas = aasx.object_store.get_identifiable(aas_id)
    check_expected_model(aas, AssetAdministrationShell)

    for submodel_ref in aas.submodel:
        try:
            submodel = submodel_ref.resolve(aasx.object_store)
        except KeyError:
            continue

        check_expected_model(submodel, model.Submodel)

        if submodel.semantic_id == MODELS3D_SEMANTIC_ID:
            model3d_list = submodel.get_referable("Model3D")  # Model3D (SML)
            model3d_list = check_expected_model(model3d_list, model.SubmodelElementList)

            for model3d_item in model3d_list:  # Model3D/[n] (SMC)
                model3d_item = check_expected_model(model3d_item, model.SubmodelElementCollection)

                file_collection = model3d_item.get_referable("File")  # Model3D/[n]/File (SMC)
                file_collection = check_expected_model(file_collection, model.SubmodelElementCollection)

                file_data = FileData()
                # Model3D/{n}/File/ConsumingApplication (SML)
                for app in _extract_consuming_applications(file_collection):
                    file_data.add_application(app)  # Model3D/[n]/File/ConsumingApplication/[n] (SMC)
                meta_data = _extract_file_versions(file_collection)  # Model3D/[n]/File/FileVersion (SML)
                if meta_data:
                    for md in meta_data:
                        file_data.add_metadata(md)  # Model3D/[n]/File/FileVersion/[n] (SMC)
                else:
                    raise ValueError("No FileVersion found")
                files.append(file_data)

        if submodel.semantic_id == MCAD_SEMANTIC_ID:
            _logger.warning("MCAD is not supported yet")
            for element in submodel:
                if element.semantic_id != MCAD_DOCUMENT_SEMANTIC_ID:
                    continue
                check_expected_model(element, model.SubmodelElementCollection)
                doc_class = element.get_referable("DocumentClassification")
                doc_class = check_expected_model(doc_class, model.SubmodelElementCollection)
                if not (get_value(doc_class, "ClassIdentifyer") == "02-02"
                        and get_value(doc_class, "ClassificationSystem") == "VDI2770:2020"):
                    continue

                doc_version = element.get_referable("DocumentVersion")
                check_expected_model(doc_version, model.SubmodelElementCollection)

                version = get_value(doc_version, "DocumentVersion")
                path = doc_version.get_referable("DigitalFile").value
                content_type = doc_version.get_referable("DigitalFile").content_type
                doc_name = doc_version.get_referable("DocumentName").value.get("en")
                file_format = mcad_doc_name_to_cadenas_format(doc_name)

                file_data = FileData()
                file_data.add_metadata(FileMetadata(
                    version,
                    path,
                    content_type,
                    file_format,
                ))
                files.append(file_data)

    return files
