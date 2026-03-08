import logging
from typing import Any, Literal

from basyx.aas import model
from basyx.aas.model import AssetAdministrationShell

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult
from aas_creo_bridge.adapters.aasx.helpers import get_value, check_expected_model, Version
from aas_creo_bridge.adapters.aasx.types import (
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
    Prefer :func:`aas_creo_bridge.adapters.aasx.helpers.get_value` for reading
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

    return files


def group_models_by_version(models: list['FileData']) -> dict[str, list['FileData']]:
    """
    Groups models into a dictionary where keys are file versions and values
    are lists of FileData objects containing that specific version's metadata.

    :param models: A list of FileData objects, each containing metadata and
                   consuming applications.
    :type models: list[FileData]
    :return: A dictionary mapping version strings to lists of FileData objects.
    :rtype: dict[str, list[FileData]]
    """
    sorted_file_data: dict[str, list[FileData]] = {}

    for m in models:
        for meta in m.metadata:
            version = meta.file_version
            # Create a new FileData object containing only this specific metadata entry
            new_entry = FileData(m.consuming_applications, [meta])

            if version in sorted_file_data:
                sorted_file_data[version].append(new_entry)
            else:
                sorted_file_data[version] = [new_entry]

    return sorted_file_data


def _matching_consuming_apps(m_consuming_apps, app_required,
                             compatibility: Literal["forward", "backward", "none"]) -> bool:
    for c_app in m_consuming_apps:
        for r_app in app_required:
            if (
                    c_app.application_name == r_app.application_name
            ):
                match compatibility:
                    case "forward":
                        if Version(c_app.application_version) <= Version(r_app.application_version):
                            return True
                    case "backward":
                        if Version(c_app.application_version) >= Version(r_app.application_version):
                            return True
                    case "none":
                        if Version(c_app.application_version) == Version(r_app.application_version):
                            return True
                    case _:
                        raise ValueError(f"Invalid compatibility mode: {compatibility}")
    return False


def filter_model_by_app(
        models: list[FileData],
        app_required: list[ConsumingApplication],
        keep_app_not_defined=True,
        compatibility: Literal["forward", "backward", "none"] = "forward",
) -> list[FileData]:
    """
    Filter models based on required applications. Use keep_app_not_defined to retain models that dont specify any
    consuming application. compatibility can either be "forward", "backward" or "none". Where forward mean an older
    file can be opened in a newer program.

    :param models: The list of models to filter.
    :type models: list[FileData]
    :param app_required: List of required applications.
    :type app_required: list[ConsumingApplication]
    :param keep_app_not_defined: Whether to keep models that don't define any application.
    :type keep_app_not_defined: bool
    :param compatibility:
    :type compatibility: Literal["forward", "backward", "none"]
    :return: A filtered list of models.
    :rtype: list[FileData]
    """
    file_data: list[FileData] = []
    for m in models:
        if not m.consuming_applications and keep_app_not_defined:
            file_data.append(m)
            continue
        if _matching_consuming_apps(m.consuming_applications, app_required, compatibility):
            file_data.append(m)
    return file_data


def find_model_for_app(
        models: list[FileData], app_required: list[ConsumingApplication]
) -> list[list[FileData]] | None:
    """
    Filter list of models for required apps. Models that don't have a required
    application specified are skipped.

    :param models: a list of FileData of all the models to search through.
    :type models: list[FileData]
    :param app_required: a list of ConsumingApplication to search for ordered by priority.
    :type app_required: list[ConsumingApplication]
    :return: a list of lists of FileData for models that have at least one of the required applications grouped by application and ordered by priority.
    :rtype: list[list[FileData]] | None
    """
    file_data: list[list[FileData]] = []
    for r_app in app_required:
        for m in models:
            file_data_for_app: list[FileData] = []
            for c_app in m.consuming_applications:
                if (
                        c_app.application_name == r_app.application_name
                        and c_app.application_version <= r_app.application_version
                ):
                    file_data_for_app.append(m)
                    break
            if file_data_for_app:
                file_data.append(file_data_for_app)
    return file_data


def find_file_for_file_format(
        models: list[FileData], filetype: list[FileFormat]
) -> list[FileData] | None:
    """
    Find files that match the specified file formats.

    :param models: List of models to search in.
    :type models: list[FileData]
    :param filetype: List of file formats to search for.
    :type filetype: list[FileFormat]
    :return: A list of models that match any of the specified file formats.
    :rtype: list[FileData] | None
    """
    file_data: list[FileData] = []
    for m in models:
        for meta in m.metadata:
            if meta.file_format == filetype:
                file_data.append(m)
                break
    return file_data
