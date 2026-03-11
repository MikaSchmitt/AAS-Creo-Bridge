from dataclasses import dataclass
from typing import Any


@dataclass
class parameter:
    parameter_name: str
    type: str
    value: Any


@dataclass
class part_parameters:
    file_name: str
    parameters: list[parameter]
