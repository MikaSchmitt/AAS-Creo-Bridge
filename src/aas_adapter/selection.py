import logging
import warnings
from typing import Literal

from .models import ConsumingApplication, FileData, FileFormat, Version

_logger = logging.getLogger(__name__)


def group_models_by_version(models: list['FileData']) -> dict[str, list['FileData']]:
    """
    Groups models into a dictionary where keys are file versions and values
    are lists of FileData objects containing that specific version's metadata.

    :param models: A list of FileData objects, each containing metadata and
                   consuming applications.
    :type models: list[FileData]
    :return: A dictionary mapping version strings to lists of FileData objects.
    :rtype: dict[str, list[FileData]]
    """
    sorted_file_data: dict[str, list[FileData]] = {}

    for m in models:
        for meta in m.metadata:
            version = meta.file_version
            new_entry = FileData(m.consuming_applications, [meta])

            if version in sorted_file_data:
                sorted_file_data[version].append(new_entry)
            else:
                sorted_file_data[version] = [new_entry]

    return sorted_file_data


def _matching_consuming_apps(m_consuming_apps, app_required,
                             compatibility: Literal["forward", "backward", "none", "full"]) -> bool:
    for c_app in m_consuming_apps:
        for r_app in app_required:
            if (
                    c_app.application_name == r_app.application_name
            ):
                match compatibility:
                    case "forward":
                        # Forward compatibility: older model/app versions are allowed for a newer requirement.
                        if Version(c_app.application_version) <= Version(r_app.application_version):
                            return True
                    case "backward":
                        # Backward compatibility: newer model/app versions are allowed for an older requirement.
                        if Version(c_app.application_version) >= Version(r_app.application_version):
                            return True
                    case "none":
                        if Version(c_app.application_version) == Version(r_app.application_version):
                            return True
                    case "full":
                        return True
                    case _:
                        raise ValueError(f"Invalid compatibility mode: {compatibility}")
    return False


def filter_model_by_app(
        models: list[FileData],
        app_required: list[ConsumingApplication],
        keep_app_not_defined=True,
        compatibility: Literal["forward", "backward", "none", "full"] = "backward",
) -> list[FileData]:
    """
    Filter models based on required applications. Use keep_app_not_defined to retain models that dont specify any
    consuming application. compatibility can either be "forward", "backward", "none" or "full":

      * "backward": an older file can be opened in a newer program
      * "forward": a newer file can be opened in an older program
      * "none": only exactly matching versions are accepted
      * "full": any version is accepted

    :param models: The list of models to filter.
    :type models: list[FileData]
    :param app_required: List of required applications.
    :type app_required: list[ConsumingApplication]
    :param keep_app_not_defined: Whether to keep models that don't define any application.
    :type keep_app_not_defined: bool
    :param compatibility:
    :type compatibility: Literal["forward", "backward", "none", "full"]
    :return: A filtered list of models.
    :rtype: list[FileData]
    """
    file_data: list[FileData] = []
    for m in models:
        if not m.consuming_applications and keep_app_not_defined:
            file_data.append(m)
            continue
        if _matching_consuming_apps(m.consuming_applications, app_required, compatibility):
            file_data.append(m)
    return file_data


def find_model_for_app(
        models: list[FileData], app_required: list[ConsumingApplication]
) -> list[list[FileData]] | None:
    """
    .. deprecated:: Use :func:`filter_model_by_app` instead.
    """
    warnings.warn(
        "find_model_for_app is deprecated; use filter_model_by_app instead",
        DeprecationWarning,
        stacklevel=2,
    )

    Filter list of models for required apps. Models that don't have a required
    application specified are skipped.

    :param models: a list of FileData of all the models to search through.
    :type models: list[FileData]
    :param app_required: a list of ConsumingApplication to search for ordered by priority.
    :type app_required: list[ConsumingApplication]
    :return: a list of lists of FileData for models that have at least one of the required applications grouped by application and ordered by priority.
    :rtype: list[list[FileData]] | None
    """
    warnings.warn(
        "old_function is deprecated; use new_function instead",
        category=DeprecationWarning,
        stacklevel=2
    )

    file_data: list[list[FileData]] = []
    for r_app in app_required:
        for m in models:
            file_data_for_app: list[FileData] = []
            for c_app in m.consuming_applications:
                if (
                        c_app.application_name == r_app.application_name
                        and c_app.application_version <= r_app.application_version
                ):
                    file_data_for_app.append(m)
                    break
            if file_data_for_app:
                file_data.append(file_data_for_app)
    return file_data


def find_file_for_file_format(
        models: list[FileData], filetype: list[FileFormat]
) -> list[FileData] | None:
    """
    Find files that match the specified file formats.

    :param models: List of models to search in.
    :type models: list[FileData]
    :param filetype: List of file formats to search for.
    :type filetype: list[FileFormat]
    :return: A list of models that match any of the specified file formats.
    :rtype: list[FileData] | None
    """
    file_data: list[FileData] = []
    for m in models:
        for meta in m.metadata:
            if meta.file_format in filetype:
                file_data.append(m)
                break
    return file_data


def _model_sort_by_app(x: FileData, apps: list[ConsumingApplication]) -> tuple[int, tuple[str, int, int, int]]:
    if not x.consuming_applications:
        return -1, ("", 0, 0, 0)

    app_names = [app.application_name for app in apps]
    current_app = x.consuming_applications[0]

    try:
        app_priority = -app_names.index(current_app.application_name)
    except ValueError:
        app_priority = -len(app_names) - 1

    # Prefer application_version if available; fall back to application_qualifier.
    version_source = getattr(current_app, "application_version", current_app.application_qualifier)
    try:
        version_tuple = Version(version_source).to_tuple()
    except (ValueError, TypeError):
        # If the version string cannot be parsed (e.g., "Creo", "MCAD"), fall back
        # to the lowest possible version so that sorting still works.
        version_tuple = ("", 0, 0, 0)

    return app_priority, version_tuple


def select_best_model(
        models: list[FileData],
        apps: list[ConsumingApplication],
        file_format: list[FileFormat] | None = None,
) -> FileData | None:
    m_grouped_by_version = group_models_by_version(models)

    sorted_keys = sorted(
        m_grouped_by_version.keys(),
        key=lambda x: Version(x).to_tuple(),
        reverse=True,
    )

    m_filtered: dict[str, list[FileData]] = {}

    for key in sorted_keys:
        models_for_version = m_grouped_by_version[key]
        m_filtered_by_app = filter_model_by_app(models_for_version, apps, False)
        m_filtered_by_app = sorted(
            m_filtered_by_app,
            key=lambda item: _model_sort_by_app(item, apps),
            reverse=True,
        )

        if m_filtered_by_app:
            m_filtered[key] = m_filtered_by_app
            continue

        if file_format:
            m_filtered_by_format = find_file_for_file_format(models_for_version, file_format)
            m_filtered[key] = m_filtered_by_format or models_for_version
        else:
            m_filtered[key] = models_for_version

    for key in sorted_keys:
        if key not in m_filtered or not m_filtered[key]:
            _logger.warning(f"No model found for version {key}")
            continue
        return m_filtered[key][0]

    return None
