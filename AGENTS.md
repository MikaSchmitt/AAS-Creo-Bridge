# AGENTS.md

## Project orientation

- This repo is a desktop bridge: Tkinter UI in `src/aas_creo_bridge` orchestrates AASX parsing in `src/aas_adapter`
  and (partly implemented) Creo/Creoson actions in `src/aas_creo_bridge/adapters/creo`.
- Runtime entrypoint is `src/aas_creo_bridge/__main__.py` -> `src/aas_creo_bridge/app/main.py`.
- `app/main.py` initializes shared singletons (`LogStore`, `AASXRegistry`, `SyncManager`) before creating `MainWindow`.

## Architecture and data flow

- AAS import flow: `ImportView._on_import_aasx` (`gui/views/import_view.py`) -> `aas_adapter.importer.import_aasx` ->
  `AASXRegistry.register` (`aas_adapter/registry.py`).
- Registry is the app event bus for AAS data: views subscribe via `get_aasx_registry().add_listener(...)` (see
  `ExplorerView` and `ConnectionsView`).
- Sync flow today: `ConnectionsView._sync_aas_to_creo` -> `SynchronizationManager.sync_aas_to_creo` (
  `app/sync_manager.py`) -> `get_models_from_aas` -> `select_best_model` -> `materialize_model_file`.
- Current sync ends after extracting a file path (prints `prepared.extracted_path`); Creo import is not yet wired in
  `SynchronizationManager`.

## Build, setup, and test workflows

- Bootstrap with `python scripts/setup.py --install-deps`.
- Use `--embedded-jre` if Java 21 is unavailable; default path expects system `java -version` major `21` (
  `scripts/setup.py`).
- CREOSON assets are downloaded/verified by SHA-256 and unpacked into repo `creoson/` (`scripts/setup.py`).
- Tests are pytest-based; `pytest.ini` sets `pythonpath = src`, so run tests from repo root.
- Useful loops: `pytest` (all), `pytest tests/app/test_sync_manager.py`, `pytest tests/aasx_adapter`.

## Code conventions to follow here

- Prefer importing adapter APIs from `aas_adapter` package root (`src/aas_adapter/__init__.py` re-exports stable
  surface).
- Shared app state is intentionally global-singleton via `app/context.py`; new UI/app code should access
  registries/loggers through `get_*` helpers.
- Logging for UI status is routed through `LogStore` (`app/logging.py`), not print statements; status bar and log window
  subscribe to log entries.
- `AASXRegistry` keeps dual indexes by path and shell id; when mutating registry state, call existing methods so
  listeners fire.
- Selection logic relies on `Version` parsing and app compatibility modes in `aas_adapter/selection.py`; keep this
  behavior in sync with tests.

## Integration points and gotchas

- External Python deps: `basyx_python_sdk`, `pyecma376_2`, `creopyson` (`requirements.txt`).
- External runtime deps: CREOSON server + Java 21 (unless embedded JRE bundle is used).
- `src/aas_creo_bridge/adapters/creo/model_import.py` is the active Creo import helper; `model_importer.py` is an
  older/incomplete duplicate.
- Several UI actions are placeholders with TODOs (`MainWindow` menu handlers, `ConnectionsView` actions); preserve
  placeholder behavior unless implementing end-to-end.
- `tests/aasx_adapter/test_selection.py` currently expects `compatibility="full"` to raise, while `selection.py`
  supports `"full"`; resolve test/code mismatch deliberately when touching compatibility logic.

