from __future__ import annotations

from pathlib import Path

from .constants import DEFAULT_JSON_PORT
from .models import CreosonSettings
from .paths import get_setvars_path

REQUIRED_SETVARS_KEYS = ("PROE_COMMON", "PROE_ENV", "JAVA_HOME", "JSON_PORT")


def render_setvars(settings: CreosonSettings) -> str:
    lines = [
        f"set PROE_COMMON={settings.proe_common}",
        f"set PROE_ENV={settings.proe_env}",
        "",
        f"set JAVA_HOME={settings.java_home}",
        "",
        f"set JSON_PORT={DEFAULT_JSON_PORT}",
        "",
    ]
    return "\r\n".join(lines)


def write_setvars_bat(settings: CreosonSettings) -> Path:
    setvars_path = get_setvars_path()
    setvars_path.write_text(render_setvars(settings), encoding="utf-8")
    return setvars_path


def _parse_setvars_content(raw: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("set "):
            continue
        key_value = stripped[4:]
        if "=" not in key_value:
            continue
        key, value = key_value.split("=", 1)
        values[key.strip().upper()] = value.strip()
    return values


def validate_setvars_bat(setvars_path: Path | None = None) -> tuple[bool, str | None]:
    path = setvars_path or get_setvars_path()
    if not path.exists():
        return False, f"Missing setvars.bat: {path}"

    parsed = _parse_setvars_content(path.read_text(encoding="utf-8"))

    for key in REQUIRED_SETVARS_KEYS:
        if not parsed.get(key):
            return False, f"Missing required variable in setvars.bat: {key}"

    if parsed.get("JSON_PORT") != str(DEFAULT_JSON_PORT):
        return False, f"JSON_PORT in setvars.bat must be {DEFAULT_JSON_PORT}."

    return True, None


def ensure_setvars_exists() -> Path:
    setvars_path = get_setvars_path()
    if setvars_path.exists():
        return setvars_path

    from .persistence import load_creoson_settings, save_creoson_settings

    settings = load_creoson_settings()
    save_creoson_settings(settings)
    return write_setvars_bat(settings)
