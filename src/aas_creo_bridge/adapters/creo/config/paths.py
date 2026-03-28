from __future__ import annotations

import sys
from pathlib import Path

from .constants import DEFAULT_SETTINGS_FILENAME


def get_project_root() -> Path:
    """Get project root, handling both frozen and source execution modes."""
    if getattr(sys, "frozen", False):
        # Running as frozen exe: go up from _internal folder
        return Path(sys.executable).parent
    else:
        # Running from source: standard relative path
        return Path(__file__).resolve().parents[5]


def get_creoson_root() -> Path:
    """Get CREOSON root folder, which is bundled in _internal for frozen builds."""
    if getattr(sys, "frozen", False):
        # For frozen exe: creoson is in _internal/creoson
        return Path(sys.executable).parent / "_internal" / "creoson"
    else:
        # For source: creoson is at project root
        return get_project_root() / "creoson"


def get_settings_path() -> Path:
    return get_creoson_root() / DEFAULT_SETTINGS_FILENAME


def get_setvars_path() -> Path:
    return get_creoson_root() / "setvars.bat"
