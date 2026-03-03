from __future__ import annotations

from types import SimpleNamespace

import aas_creo_bridge.adapters.aasx.get_models as get_models_mod


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
    monkeypatch.setattr(get_models_mod, "AssetAdministrationShell", _FakeAssetAdministrationShell)
    return fake_model


def test_get_models_from_aas_extracts_consuming_apps_and_file_metadata(monkeypatch):
    fake_model = _patch_model(monkeypatch)
    models3d_semantic = fake_model.ModelReference(
        (fake_model.Key(type_=fake_model.KeyTypes.SUBMODEL, value="https://admin-shell.io/idta/Models3D/1/0"),),
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
            "DigitalFile": SimpleNamespace(value="model.step", content_type="application/step"),
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
        (fake_model.Key(type_=fake_model.KeyTypes.SUBMODEL, value="https://admin-shell.io/idta/Models3D/1/0"),),
        type_=fake_model.Submodel,
    )

    file_collection = _FakeSubmodelElementCollection({"ConsumingApplication": _FakeSubmodelElementList([])})
    model3d = _FakeSubmodelElementCollection({"File": file_collection})
    model3d_list = _FakeSubmodelElementList([model3d])
    submodel = _FakeSubmodel(models3d_semantic, {"Model3D": model3d_list})
    aas = _FakeAssetAdministrationShell([_FakeSmRef(submodel)])
    aasx = SimpleNamespace(object_store=_FakeStore(aas))

    out = get_models_mod.get_models_from_aas(aasx, "aas_1")

    assert out == []
