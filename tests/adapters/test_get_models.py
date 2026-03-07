from __future__ import annotations

import pytest

from types import SimpleNamespace

import aas_creo_bridge.adapters.aasx.get_models as get_models_mod
from aas_creo_bridge.adapters.aasx import group_models_by_version, FileMetadata, FileData


class _FakeAssetAdministrationShell:
    def __init__(self, submodel):
        self.submodel = submodel


class _FakeSubmodel:
    def __init__(self, semantic_id, referables):
        self.semantic_id = semantic_id
        self._referables = referables

    def get_referable(self, key):
        if key not in self._referables:
            raise KeyError(key)
        return self._referables[key]


class _FakeSubmodelElementList:
    def __init__(self, value):
        self.value = value

    def __iter__(self):
        return iter(self.value)


class _FakeSubmodelElementCollection:
    def __init__(self, referables):
        self._referables = referables

    def get_referable(self, key):
        if key not in self._referables:
            raise KeyError(key)
        return self._referables[key]


class _FakeSmRef:
    def __init__(self, submodel):
        self._submodel = submodel

    def resolve(self, _object_store):
        return self._submodel


class _FakeStore:
    def __init__(self, aas):
        self._aas = aas

    def get_identifiable(self, _aas_id):
        return self._aas

def _patch_model(monkeypatch):
    key_types = SimpleNamespace(SUBMODEL="SUBMODEL")
    fake_model = SimpleNamespace(
        Submodel=_FakeSubmodel,
        SubmodelElementList=_FakeSubmodelElementList,
        SubmodelElementCollection=_FakeSubmodelElementCollection,
        KeyTypes=key_types,
        Key=lambda type_, value: (type_, value),
        ModelReference=lambda key_tuple, type_: ("ModelReference", key_tuple, type_),
    )
    monkeypatch.setattr(get_models_mod, "model", fake_model)
    monkeypatch.setattr(
        get_models_mod, "AssetAdministrationShell", _FakeAssetAdministrationShell
    )

    # Patch semantic-id constants too: they were created with the real basyx model at import time.
    monkeypatch.setattr(
        get_models_mod,
        "MODELS3D_SEMANTIC_ID",
        fake_model.ModelReference(
            (
                fake_model.Key(
                    type_=fake_model.KeyTypes.SUBMODEL,
                    value="https://admin-shell.io/idta/Models3D/1/0",
                ),
            ),
            type_=fake_model.Submodel,
        ),
    )
    monkeypatch.setattr(
        get_models_mod,
        "MCAD_SEMANTIC_ID",
        fake_model.ModelReference(
            (
                fake_model.Key(
                    type_=fake_model.KeyTypes.SUBMODEL,
                    value="https://admin-shell.io/sandbox/idta/handover/MCAD/0/1/",
                ),
            ),
            type_=fake_model.Submodel,
        ),
    )

    return fake_model


def test_get_models_from_aas_extracts_consuming_apps_and_file_metadata(monkeypatch):
    fake_model = _patch_model(monkeypatch)
    models3d_semantic = fake_model.ModelReference(
        (
            fake_model.Key(
                type_=fake_model.KeyTypes.SUBMODEL,
                value="https://admin-shell.io/idta/Models3D/1/0",
            ),
        ),
        type_=fake_model.Submodel,
    )

    app = _FakeSubmodelElementCollection(
        {
            "ApplicationName": SimpleNamespace(value="Creo"),
            "ApplicationVersion": SimpleNamespace(value="10"),
            "ApplicationQualifier": SimpleNamespace(value="MCAD"),
        }
    )
    consuming_apps = _FakeSubmodelElementList([app])
    file_format = _FakeSubmodelElementCollection(
        {
            "FormatName": SimpleNamespace(value="STEP"),
            "FormatVersion": SimpleNamespace(value="AP242"),
            "FormatQualifier": SimpleNamespace(value="exchange"),
        }
    )
    file_version = _FakeSubmodelElementCollection(
        {
            "FileVersionId": SimpleNamespace(value="v1"),
            "FileFormat": file_format,
            "DigitalFile": SimpleNamespace(
                value="model.step", content_type="application/step"
            ),
        }
    )
    file_versions = _FakeSubmodelElementList([file_version])
    file_collection = _FakeSubmodelElementCollection(
        {"ConsumingApplication": consuming_apps, "FileVersion": file_versions}
    )
    model3d = _FakeSubmodelElementCollection({"File": file_collection})
    model3d_list = _FakeSubmodelElementList([model3d])
    submodel = _FakeSubmodel(models3d_semantic, {"Model3D": model3d_list})
    aas = _FakeAssetAdministrationShell([_FakeSmRef(submodel)])
    aasx = SimpleNamespace(object_store=_FakeStore(aas))

    out = get_models_mod.get_models_from_aas(aasx, "aas_1")

    assert out is not None
    assert len(out) == 1
    assert len(out[0].consuming_applications) == 1
    assert out[0].consuming_applications[0].application_name == "Creo"
    assert len(out[0].metadata) == 1
    assert out[0].metadata[0].file_format.format_name == "STEP"
    assert out[0].metadata[0].filepath == "model.step"


def test_get_models_from_aas_skips_model_when_file_version_missing(monkeypatch):
    fake_model = _patch_model(monkeypatch)
    models3d_semantic = fake_model.ModelReference(
        (
            fake_model.Key(
                type_=fake_model.KeyTypes.SUBMODEL,
                value="https://admin-shell.io/idta/Models3D/1/0",
            ),
        ),
        type_=fake_model.Submodel,
    )

    file_collection = _FakeSubmodelElementCollection(
        {"ConsumingApplication": _FakeSubmodelElementList([])}
    )
    model3d = _FakeSubmodelElementCollection({"File": file_collection})
    model3d_list = _FakeSubmodelElementList([model3d])
    submodel = _FakeSubmodel(models3d_semantic, {"Model3D": model3d_list})
    aas = _FakeAssetAdministrationShell([_FakeSmRef(submodel)])
    aasx = SimpleNamespace(object_store=_FakeStore(aas))

    try:
        out = get_models_mod.get_models_from_aas(aasx, "aas_1")
    except ValueError:
        assert True
    else:
        assert False, "Expected ValueError"

# Fixtures provide reusable test data
@pytest.fixture
def sample_metadata():
    return {
        "v1": FileMetadata(file_version="1.0", filepath="", file_content_type="", file_format=""),
        "v2": FileMetadata(file_version="2.0", filepath="", file_content_type="", file_format="")
    }

def test_empty_input():
    """Verify handling of empty lists."""
    assert group_models_by_version([]) == {}

def test_single_model_grouping(sample_metadata):
    """Verify a single model is grouped correctly by its version."""
    model = FileData(["AppA"], [sample_metadata["v1"]])
    result = group_models_by_version([model])

    assert "1.0" in result
    assert len(result["1.0"]) == 1
    assert result["1.0"][0].metadata[0].file_version == "1.0"

def test_multi_version_model(sample_metadata):
    """Verify one model with two versions splits into both groups."""
    model = FileData(["AppA"], [sample_metadata["v1"], sample_metadata["v2"]])
    result = group_models_by_version([model])

    assert len(result) == 2
    assert "1.0" in result and "2.0" in result

# Parametrization allows testing multiple cases in one function
@pytest.mark.parametrize("app_list", [
    (["App1"]),
    (["App1", "App2"]),
    ([])
])
def test_app_persistence(app_list, sample_metadata):
    """Ensure consuming_applications are preserved during grouping."""
    model = FileData(app_list, [sample_metadata["v1"]])
    result = group_models_by_version([model])
    assert result["1.0"][0].consuming_applications == app_list
