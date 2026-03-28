from __future__ import annotations

import json
from dataclasses import asdict

from .defaults import DEFAULT_JSON_PORT, get_default_settings
from .paths import get_settings_path


def load_creoson_settings() -> CreosonSettings:
    from .setvars import CreosonSettings

    settings_path = get_settings_path()
    defaults = get_default_settings()

    if not settings_path.exists():
        return defaults

    with settings_path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    return CreosonSettings(
        proe_common=str(data.get("proe_common", defaults.proe_common)),
        proe_env=str(data.get("proe_env", defaults.proe_env)),
        java_home=str(data.get("java_home", defaults.java_home)),
        json_port=DEFAULT_JSON_PORT,
    )


def save_creoson_settings(settings: CreosonSettings) -> None:
    settings_path = get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(settings)
    payload["json_port"] = DEFAULT_JSON_PORT

    with settings_path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)

