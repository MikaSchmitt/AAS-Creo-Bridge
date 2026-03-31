import logging

import creopyson

from .types import Parameter, PartParameters

_logger = logging.getLogger(__name__)


def set_parameter(
        client: creopyson.Client,
        file_name: str,
        parameter: Parameter,
        *,
        designate: bool | None = True,
        no_create: bool | None = None,
) -> None:
    """
    Set a single parameter on a Creo model via Creoson.
    """
    if not file_name or not file_name.strip():
        raise ValueError("file_name must be provided.")
    if not parameter.name:
        raise ValueError("Parameter name must be provided.")

    try:
        client.parameter_set(
            file_=file_name,
            name=parameter.name,
            value=parameter.value,
            type_=parameter.type or None,
            designate=designate,
            no_create=no_create,
        )
        _logger.info("Updated %s -> %s: %s", file_name, parameter.name, parameter.value)
    except Exception as e:
        _logger.error(
            "Could not set parameter %s for %s: %r",
            parameter.name,
            file_name,
            e,
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to set parameter '{parameter.name}' for '{file_name}'"
        ) from e


def set_part_parameters(
        client: creopyson.Client,
        part: PartParameters,
        *,
        designate: bool | None = True,
        no_create: bool | None = None,
) -> None:
    """
    Set all parameters for a part using the PartParameters dataclass.
    """
    if not part.file_name or not part.file_name.strip():
        raise ValueError("part.file_name must be provided.")
    if not part.parameters:
        raise ValueError("part.parameters must not be empty.")

    for param in part.parameters:
        set_parameter(
            client,
            file_name=part.file_name,
            parameter=param,
            designate=designate,
            no_create=no_create,
        )
