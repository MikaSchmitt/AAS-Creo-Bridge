from __future__ import annotations

from dataclasses import dataclass

from aas_creo_bridge.config.constants import DEFAULT_JSON_PORT


@dataclass(slots=True)
class CreosonSettings:
    proe_common: str
    proe_env: str
    java_home: str
    json_port: int = DEFAULT_JSON_PORT

