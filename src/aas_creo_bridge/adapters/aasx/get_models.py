import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from basyx.aas import model
from basyx.aas.model import AssetAdministrationShell

from aas_creo_bridge.adapters.aasx.aasx_importer import AASXImportResult

_logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class ConsumingApplication:
    application_name: str
    application_version: str
    application_qualifier: str

@dataclass(frozen=True, slots=True)
class FileMetadata:
    file_version: str
    format_name: str
    format_version: str
    format_qualifier: str
    filepath: str
    file_content_type: str

@dataclass(slots=True)
class FileData:
    consuming_applications: list[ConsumingApplication] = field(default_factory=list)
    metadata: list[FileMetadata] = field(default_factory=list)

    def add_application(self, app: ConsumingApplication) -> "FileData":
        self.consuming_applications.append(app)
        return self

    def add_metadata(self, meta: FileMetadata) -> "FileData":
        self.metadata.append(meta)
        return self

def _get_element(obj: Any, prop: str) -> Any:
    return obj.value.get('id_short', prop)


def get_models_from_aas(aasx: AASXImportResult, aas_id: str) -> list[FileData] | None:
    files: list[FileData] = []

    aas = aasx.object_store.get_identifiable(aas_id)
    assert isinstance(aas, AssetAdministrationShell)
    for sm_ref in aas.submodel:
        try:
            sm = sm_ref.resolve(aasx.object_store)
        except KeyError:
            continue
        if not isinstance(sm, model.Submodel):
            continue

        if sm.semantic_id == model.ModelReference(
                (model.Key(type_=model.KeyTypes.SUBMODEL, value="https://admin-shell.io/idta/Models3D/1/0"),),
                type_=model.Submodel,
        ):
            model3ds = sm.get_referable("Model3D")
            assert isinstance(model3ds, model.SubmodelElementList)
            for model3d in model3ds:
                assert isinstance(model3d, model.SubmodelElementCollection)
                file_data = FileData()
                consuming_applications = []

                file = model3d.get_referable("File")
                assert isinstance(file, model.SubmodelElementCollection)
                try:
                    consuming_applications = file.get_referable("ConsumingApplication")
                except KeyError:
                    pass
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    continue
                for consuming_application in consuming_applications.value:
                    application_name = consuming_application.get_referable('ApplicationName').value
                    application_version = consuming_application.get_referable('ApplicationVersion').value
                    application_qualifier = consuming_application.get_referable('ApplicationQualifier').value
                    file_data.add_application(
                        ConsumingApplication(application_name, application_version, application_qualifier))
                try:
                    file_versions = file.get_referable('FileVersion')
                except KeyError:
                    continue
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    continue
                for file_version in file_versions.value:
                    version = file_version.get_referable('FileVersionId').value
                    file_format = file_version.get_referable('FileFormat')
                    format_name = file_format.get_referable('FormatName').value
                    format_version = file_format.get_referable('FormatVersion').value
                    format_qualifier = file_format.get_referable('FormatQualifier').value
                    filepath, file_content_type = "", ""
                    try:
                        digital_file = file_version.get_referable('DigitalFile')
                        filepath = digital_file.value
                        file_content_type = digital_file.content_type
                    except KeyError:
                        pass    # DigitalFile is not mandatory
                    except Exception as e:
                        print(f"Exception occurred: {e}")
                    try:
                        external_file = file_version.get_referable('ExternalFile')
                        logging.warning(f"AAS contains ExternalFile: {external_file} \n External files are not supported yet")
                    except KeyError:
                        pass    # ExternalFile is not mandatory
                    except Exception as e:
                        print(f"Exception occurred: {e}")
                    file_data.add_metadata(
                        FileMetadata(version, format_name, format_version, format_qualifier, filepath,
                                     file_content_type))

                files.append(file_data)

        # TODO: MCAD
        if sm.semantic_id == model.ModelReference(
                (model.Key(type_=model.KeyTypes.SUBMODEL, value="https://admin-shell.io/sandbox/idta/handover/MCAD/0/1/"),),
                type_=model.Submodel,
        ):
            _logger.warning("MCAD is not supported yet")

    return files