import logging
from typing import Any

from basyx.aas import model
from basyx.aas.model import AssetAdministrationShell

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult

from aas_creo_bridge.adapters.aasx.types import FileData, ConsumingApplication, FileMetadata, FileFormat

_logger = logging.getLogger(__name__)

def _get_element(obj: Any, prop: str) -> Any:
    return obj.value.get('id_short', prop)


MODELS3D_SEMANTIC_ID = model.ModelReference(
    (model.Key(type_=model.KeyTypes.SUBMODEL, value="https://admin-shell.io/idta/Models3D/1/0"),),
    type_=model.Submodel,
)

MCAD_SEMANTIC_ID = model.ModelReference(
    (model.Key(type_=model.KeyTypes.SUBMODEL, value="https://admin-shell.io/sandbox/idta/handover/MCAD/0/1/"),),
    type_=model.Submodel,
)


def _extract_consuming_applications(file_collection: model.SubmodelElementCollection, file_data: FileData) -> None:
    try:
        consuming_apps = file_collection.get_referable("ConsumingApplication")
    except KeyError:
        return
    except Exception:
        _logger.exception("Failed to read ConsumingApplication")
        return

    if not hasattr(consuming_apps, "value"):
        return

    for app in consuming_apps.value:
        file_data.add_application(
            ConsumingApplication(
                app.get_referable("ApplicationName").value,
                app.get_referable("ApplicationVersion").value,
                app.get_referable("ApplicationQualifier").value,
            )
        )


def _extract_file_versions(file_collection: model.SubmodelElementCollection, file_data: FileData) -> None:
    try:
        file_versions = file_collection.get_referable("FileVersion")
    except KeyError:
        return # DigitalFile is optional
    except Exception:
        _logger.exception("Failed to read FileVersion")
        return

    if not hasattr(file_versions, "value"):
        return

    for version_item in file_versions.value:
        version = version_item.get_referable("FileVersionId").value
        file_format = version_item.get_referable("FileFormat")
        format_name = file_format.get_referable("FormatName").value
        format_version = file_format.get_referable("FormatVersion").value
        format_qualifier = file_format.get_referable("FormatQualifier").value

        filepath, file_content_type = "", ""
        try:
            digital_file = version_item.get_referable("DigitalFile")
            filepath = digital_file.value
            file_content_type = digital_file.content_type
        except KeyError:
            pass  # DigitalFile is optional
        except Exception:
            _logger.exception("Failed to read DigitalFile")

        try:
            external_file = version_item.get_referable("ExternalFile")
            _logger.warning(
                "AAS contains ExternalFile: %s\nExternal files are not supported yet",
                external_file,
            )
        except KeyError:
            pass  # ExternalFile is optional
        except Exception:
            _logger.exception("Failed to read ExternalFile")

        file_data.add_metadata(
            FileMetadata(
                version,
                filepath,
                file_content_type,
                FileFormat(format_name, format_version, format_qualifier),
            )
        )


def get_models_from_aas(aasx: AASXImportResult, aas_id: str) -> list[FileData]:
    files: list[FileData] = []

    aas = aasx.object_store.get_identifiable(aas_id)
    if not isinstance(aas, AssetAdministrationShell):
        return files

    for submodel_ref in aas.submodel:
        try:
            submodel = submodel_ref.resolve(aasx.object_store)
        except KeyError:
            continue

        if not isinstance(submodel, model.Submodel):
            continue

        if submodel.semantic_id == MODELS3D_SEMANTIC_ID:
            model3d_list = submodel.get_referable("Model3D")
            if not isinstance(model3d_list, model.SubmodelElementList):
                continue

            for model3d_item in model3d_list:
                if not isinstance(model3d_item, model.SubmodelElementCollection):
                    continue

                file_collection = model3d_item.get_referable("File")
                if not isinstance(file_collection, model.SubmodelElementCollection):
                    continue

                file_data = FileData()
                _extract_consuming_applications(file_collection, file_data)
                _extract_file_versions(file_collection, file_data)
                files.append(file_data)

        if submodel.semantic_id == MCAD_SEMANTIC_ID:
            _logger.warning("MCAD is not supported yet")

    return files

def find_model_for_app(models: list[FileData], app_required: list[ConsumingApplication]) -> list[list[FileData]] | None:
    """
    :param models: a list of FileData of all the models to search through
    :param app_required: a list of ConsumingApplication to search for ordered by priority
    :return: a list of lists of FileData for models that have at least one of the required applications grouped by application and ordered by priority
    Filter list of models for required apps. Models that don't have a required application specified are skipped.
    """
    file_data: list[list[FileData]] = [[]]
    for m in models:
        for r_app in app_required:
            file_data_for_app: list[FileData] = []
            for c_app in m.consuming_applications:
                if (c_app.application_name == r_app.application_name
                    and c_app.application_version <= r_app.application_version):
                    file_data_for_app.append(m)
                    break
            file_data.append(file_data_for_app)
    return file_data

def find_file_for_file_format(models: list[FileData], filetype: list[FileFormat]) -> list[FileData] | None:
    file_data: list[FileData] = []
    for m in models:
        for meta in m.metadata:
            if meta.file_format == filetype:
                file_data.append(m)
                break
    return file_data