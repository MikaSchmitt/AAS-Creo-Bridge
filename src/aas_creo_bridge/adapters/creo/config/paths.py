from __future__ import annotations

from pathlib import Path

from .defaults import DEFAULT_SETTINGS_FILENAME


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_creoson_root() -> Path:
    return get_project_root() / "creoson"


def get_settings_path() -> Path:
    return get_creoson_root() / DEFAULT_SETTINGS_FILENAME


def get_setvars_path() -> Path:
    return get_creoson_root() / "setvars.bat"

