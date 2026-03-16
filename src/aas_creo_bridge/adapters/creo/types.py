from dataclasses import dataclass
from typing import Any


@dataclass
class Parameter:
    parameter_name: str
    type: str
    value: Any


@dataclass
class PartParameters:
    file_name: str
    parameters: list[Parameter]
