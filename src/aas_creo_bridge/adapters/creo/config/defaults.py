from __future__ import annotations

import os
import platform
from pathlib import Path

# Constants
DEFAULT_JSON_PORT = 9056
DEFAULT_SETTINGS_FILENAME = "bridge_settings.json"


def _detect_proe_common() -> str:
    ptc_root = Path("C:/Program Files/PTC")
    if not ptc_root.exists():
        return ""

    candidates: list[Path] = []
    for creo_dir in ptc_root.glob("Creo*"):
        common_dir = creo_dir / "Common Files"
        if common_dir.is_dir():
            candidates.append(common_dir)

    if not candidates:
        return ""

    return str(sorted(candidates)[-1])


def _detect_proe_env() -> str:
    machine = platform.machine().lower()
    return "x86e_win64" if "64" in machine else "x86e_win32"


def _detect_java_home() -> str:
    from .paths import get_creoson_root

    if (get_creoson_root() / "jre").is_dir():
        return "jre"

    for candidate in (
        os.environ.get("JAVA_HOME"),
        "C:/Program Files/Java/jre21",
        "C:/Program Files (x86)/Java/jre21",
    ):
        if candidate and Path(candidate).is_dir():
            return candidate

    return "C:/Program Files/Java/jre21"


def get_default_settings() -> CreosonSettings:
    """
    Get default CREOSON bridge settings specific to the current device.

    The returned settings are assembled from environment-specific defaults:
        proe_common: Newest ``Common Files`` directory under
            ``C:/Program Files/PTC/Creo*`` when available.
        proe_env: ``x86e_win64`` on 64-bit machines, otherwise
            ``x86e_win32``.
        java_home: Bundled ``jre`` under the CREOSON root when present,
            otherwise a discovered system Java path, otherwise a fallback path.
        json_port: Fixed default JSON server port.

    Returns:
        CreosonSettings: Settings object populated with detected defaults.
    """
    from .setvars import CreosonSettings

    return CreosonSettings(
        proe_common=_detect_proe_common(),
        proe_env=_detect_proe_env(),
        java_home=_detect_java_home(),
        json_port=DEFAULT_JSON_PORT,
    )
