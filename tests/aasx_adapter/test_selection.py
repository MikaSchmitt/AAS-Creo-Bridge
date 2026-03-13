from __future__ import annotations

import pytest

from aas_adapter import ConsumingApplication, FileData
from aas_adapter import filter_model_by_app


def test_filter_model_by_app_returns_only_matching_models():
    required_app = ConsumingApplication("Creo Parametric", "10", "Creo 10")
    matching_model = FileData(
        consuming_applications=[ConsumingApplication("Creo Parametric", "9", "Creo 10")],
        metadata=[],
    )
    non_matching_model = FileData(
        consuming_applications=[ConsumingApplication("NX", "2206", "NX 2206")],
        metadata=[],
    )

    result = filter_model_by_app(
        [matching_model, non_matching_model],
        [required_app],
    )

    assert result == [matching_model]


def test_filter_model_by_app_keeps_models_without_apps_by_default():
    required_app = ConsumingApplication("Creo Parametric", "10", "Creo 10")
    model_without_apps = FileData(consuming_applications=[], metadata=[])
    non_matching_model = FileData(
        consuming_applications=[ConsumingApplication("NX", "2206", "NX 2206")],
        metadata=[],
    )

    result = filter_model_by_app(
        [model_without_apps, non_matching_model],
        [required_app],
    )

    assert result == [model_without_apps]


def test_filter_model_by_app_excludes_models_without_apps_when_disabled():
    required_app = ConsumingApplication("Creo Parametric", "10", "Creo 10")
    model_without_apps = FileData(consuming_applications=[], metadata=[])

    result = filter_model_by_app(
        [model_without_apps],
        [required_app],
        keep_app_not_defined=False,
    )

    assert result == []


@pytest.mark.parametrize(
    ("compatibility", "model_version", "required_version", "expected_count"),
    [
        ("forward", "9", "10", 1),
        ("backward", "11", "10", 1),
        ("none", "11", "10", 0),
    ],
)
def test_filter_model_by_app_respects_compatibility_mode(
        compatibility: str,
        model_version: str,
        required_version: str,
        expected_count: int,
):
    required_app = ConsumingApplication("Creo Parametric", required_version, "Creo")
    model = FileData(
        consuming_applications=[ConsumingApplication("Creo Parametric", model_version, "Creo")],
        metadata=[],
    )

    result = filter_model_by_app(
        [model],
        [required_app],
        compatibility=compatibility,
    )

    assert len(result) == expected_count


def test_filter_model_by_app_raises_for_invalid_compatibility_mode():
    required_app = ConsumingApplication("Creo Parametric", "10", "Creo")
    model = FileData(
        consuming_applications=[ConsumingApplication("Creo Parametric", "10", "Creo")],
        metadata=[],
    )

    with pytest.raises(ValueError, match="compatibility"):
        filter_model_by_app(
            [model],
            [required_app],
            compatibility="full",
        )
