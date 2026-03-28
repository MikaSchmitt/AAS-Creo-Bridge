from dataclasses import dataclass

from .constants import DEFAULT_JSON_PORT


@dataclass(slots=True)
class CreosonSettings:
    proe_common: str
    proe_env: str
    java_home: str
    json_port: int = DEFAULT_JSON_PORT
