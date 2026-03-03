# tests/adapters/test_aasx_importer.py
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import aas_creo_bridge.adapters.aasx.aasx_importer as importer_mod


class _FakeAASXReader:
    """
    Test double for basyx.aas.adapter.AASXReader that behaves as a context manager.
    Configure via constructor args.
    """

    def __init__(
        self,
        path: Path,
        *,
        identifiers: set[str] | None = None,
        core_properties: Any = None,
        thumbnail: bytes | None = None,
        raise_on_enter: Exception | None = None,
        raise_on_read_into: Exception | None = None,
    ) -> None:
        self.path = path
        self._identifiers = identifiers if identifiers is not None else set()
        self._core_properties = core_properties
        self._thumbnail = thumbnail
        self._raise_on_enter = raise_on_enter
        self._raise_on_read_into = raise_on_read_into

        self.read_into_called_with: dict[str, Any] | None = None

    def __enter__(self) -> "_FakeAASXReader":
        if self._raise_on_enter:
            raise self._raise_on_enter
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False  # don't suppress exceptions

    def read_into(self, *, object_store: Any, file_store: Any) -> set[str]:
        self.read_into_called_with = {"object_store": object_store, "file_store": file_store}
        if self._raise_on_read_into:
            raise self._raise_on_read_into
        return set(self._identifiers)

    def get_core_properties(self) -> Any:
        return self._core_properties

    def get_thumbnail(self) -> bytes | None:
        return self._thumbnail


def test_import_aasx_raises_filenotfound_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.aasx"
    with pytest.raises(FileNotFoundError, match=r"AASX file not found:"):
        importer_mod.import_aasx(missing)


def test_import_aasx_raises_filenotfound_for_directory(tmp_path: Path) -> None:
    folder = tmp_path / "not_a_file.aasx"
    folder.mkdir()
    with pytest.raises(FileNotFoundError, match=r"AASX file not found:"):
        importer_mod.import_aasx(folder)


def test_import_aasx_success_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    aasx_path = tmp_path / "sample.aasx"
    aasx_path.write_bytes(b"not-a-real-aasx-but-path-exists")

    fake_identifiers = {"shell-1", "shell-2"}
    fake_core_props = SimpleNamespace(title="t")
    fake_thumbnail = b"\x89PNG..."

    # Make object_store/file_store predictable test doubles.
    fake_object_store = object()
    fake_file_store = object()

    monkeypatch.setattr(importer_mod, "DictObjectStore", lambda: fake_object_store)
    monkeypatch.setattr(importer_mod, "DictSupplementaryFileContainer", lambda: fake_file_store)

    # Force shell discovery to a known result (unit-testing import_aasx wiring, not shell parsing here).
    monkeypatch.setattr(importer_mod, "_discover_shells", lambda identifiers, objects: ["DISCOVERED"])

    # Patch AASXReader to our fake reader.
    def _reader_factory(path: Path) -> _FakeAASXReader:
        return _FakeAASXReader(
            path,
            identifiers=fake_identifiers,
            core_properties=fake_core_props,
            thumbnail=fake_thumbnail,
        )

    monkeypatch.setattr(importer_mod, "AASXReader", _reader_factory)

    result = importer_mod.import_aasx(aasx_path)

    assert isinstance(result, importer_mod.AASXImportResult)
    assert result.path == aasx_path
    assert result.object_store is fake_object_store
    assert result.file_store is fake_file_store
    assert result.metadata is fake_core_props
    assert result.thumbnail == fake_thumbnail
    assert result.shells == ["DISCOVERED"]


def test_import_aasx_wraps_reader_errors_as_valueerror_and_logs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog) -> None:
    aasx_path = tmp_path / "broken.aasx"
    aasx_path.write_bytes(b"xxx")

    # Keep store creation simple
    monkeypatch.setattr(importer_mod, "DictObjectStore", lambda: object())
    monkeypatch.setattr(importer_mod, "DictSupplementaryFileContainer", lambda: object())

    # Make reader fail on enter (could also fail on read_into; both should be wrapped).
    def _reader_factory(path: Path) -> _FakeAASXReader:
        return _FakeAASXReader(path, raise_on_enter=RuntimeError("boom"))

    monkeypatch.setattr(importer_mod, "AASXReader", _reader_factory)

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match=r"Not a valid AASX/zip file:"):
            importer_mod.import_aasx(aasx_path)

    # Ensure we emitted an error log mentioning the path (message format is part of behavior here).
    assert any(
        (rec.levelname == "ERROR" and "AASX import failed for" in rec.message and str(aasx_path) in rec.message)
        for rec in caplog.records
    )


def test_discover_shells_returns_empty_when_no_identifiers() -> None:
    class _Store:
        def get_identifiable(self, identifier: str) -> object:  # pragma: no cover
            raise AssertionError("Should not be called when identifiers is empty")

    assert importer_mod._discover_shells(set(), _Store()) == []


def test_discover_shells_filters_only_aas_shell_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch the AssetAdministrationShell type check to something we control.
    class _FakeShell:
        def __init__(self) -> None:
            self.id_short = "x"
            self.id = "y"

    monkeypatch.setattr(importer_mod.model, "AssetAdministrationShell", _FakeShell)

    objects_by_id = {
        "id-shell": _FakeShell(),
        "id-not-shell": object(),
    }

    class _Store:
        def get_identifiable(self, identifier: str) -> object:
            return objects_by_id[identifier]

    out = importer_mod._discover_shells({"id-shell", "id-not-shell"}, _Store())
    assert out == ["id-shell"]
