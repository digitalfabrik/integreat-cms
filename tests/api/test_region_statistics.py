from __future__ import annotations

from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.client import Client
from django.urls import reverse

from integreat_cms.api.v3.region_statistics import Statistics
from integreat_cms.cms.models import ApiToken, Region, RegionCondition
from integreat_cms.cms.utils import region_condition_utils
from integreat_cms.cms.utils.region_condition_utils import (
    cacheops_disabled,
    compute_region_condition,
    METRICS,
    update_region_conditions,
)


def _token_for(username: str) -> str:
    """
    Create an API token for the given user

    :param username: The username of the token's user
    :return: The plaintext token
    """
    user = get_user_model().objects.get(username=username)
    _token, plaintext = ApiToken.create_token(user, f"test-{username}")
    return plaintext


def _get_statistics(token: str, region_slug: str = "augsburg") -> dict:
    """
    Request the statistics of a region

    :param token: The plaintext API token
    :param region_slug: The slug of the region
    :return: The response
    """
    endpoint = reverse("api:region_statistics", kwargs={"region_slug": region_slug})
    return Client().get(endpoint, headers={"authorization": f"Bearer {token}"})


@pytest.mark.django_db
def test_statistics_before_first_computation(load_test_data: None) -> None:
    """
    Before the nightly computation ran, the metrics are ``None`` instead of being computed on request.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    RegionCondition.objects.all().delete()

    response = _get_statistics(_token_for("root"))

    assert response.status_code == 200
    data = response.json()
    # The response has exactly the shape of the typed dictionary, and every stored metric is in it
    assert set(data) == set(Statistics.__annotations__)
    assert set(METRICS) <= set(data)
    assert data["computed_at"] is None
    assert all(data[metric] is None for metric in METRICS)
    region = Region.objects.get(slug="augsburg")
    assert data["mt_budget_remaining"] == region.mt_budget_remaining


@pytest.mark.django_db
def test_statistics_return_the_stored_values(load_test_data: None) -> None:
    """
    After the computation, the endpoint returns the stored values, which match the export.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    updated, failed = update_region_conditions()

    assert updated > 0
    assert failed == 0
    region = Region.objects.get(slug="augsburg")
    expected = compute_region_condition(region)
    data = _get_statistics(_token_for("root")).json()
    assert data["computed_at"] is not None
    assert {metric: data[metric] for metric in METRICS} == expected


@pytest.mark.django_db
def test_statistics_are_not_computed_on_request(load_test_data: None) -> None:
    """
    Reading the statistics must never trigger the expensive computation.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with patch.object(region_condition_utils, "compute_region_condition") as compute:
        _get_statistics(_token_for("root"))

    compute.assert_not_called()


@pytest.mark.django_db
def test_failing_region_does_not_stop_the_others(load_test_data: None) -> None:
    """
    One broken region is logged and skipped, the others are still updated.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    RegionCondition.objects.all().delete()
    original = region_condition_utils.compute_region_condition

    def fail_for_augsburg(region: Region) -> dict[str, int]:
        if region.slug == "augsburg":
            raise RuntimeError("broken region")
        return original(region)

    with patch.object(
        region_condition_utils,
        "compute_region_condition",
        side_effect=fail_for_augsburg,
    ):
        updated, failed = update_region_conditions()

    assert failed == 1
    assert updated > 0
    assert not RegionCondition.objects.filter(region__slug="augsburg").exists()
    assert RegionCondition.objects.count() == updated


@pytest.mark.django_db
def test_command_fails_when_a_region_failed(load_test_data: None) -> None:
    """
    The management command reports a failed region instead of exiting successfully.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with (
        patch.object(
            region_condition_utils,
            "compute_region_condition",
            side_effect=RuntimeError("broken region"),
        ),
        pytest.raises(CommandError),
    ):
        call_command("update_region_conditions")


def test_cacheops_is_disabled_during_the_computation() -> None:
    """
    The computation bypasses the query cache, which would otherwise be filled with huge querysets.
    """
    with cacheops_disabled():
        assert settings.CACHEOPS_ENABLED is False


@pytest.mark.django_db
def test_requires_authentication(load_test_data: None) -> None:
    """
    Requests without a valid token are rejected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_statistics", kwargs={"region_slug": "augsburg"})

    assert Client().get(endpoint).status_code == 403
    assert _get_statistics("invalid.token").status_code == 403


@pytest.mark.django_db
def test_requires_permission(load_test_data: None) -> None:
    """
    A token of a user without ``cms.view_region`` is rejected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    unprivileged = next(
        user
        for user in get_user_model().objects.filter(is_superuser=False, is_active=True)
        if not user.has_perm("cms.view_region")
    )
    _token, plaintext = ApiToken.create_token(unprivileged, "test-unprivileged")

    assert _get_statistics(plaintext).status_code == 403


@pytest.mark.django_db
def test_only_get_is_allowed(load_test_data: None) -> None:
    """
    The statistics are read-only.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_statistics", kwargs={"region_slug": "augsburg"})
    response = Client().post(
        endpoint,
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_unknown_region_returns_404(load_test_data: None) -> None:
    """
    An unknown region slug results in a 404.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    assert _get_statistics(_token_for("root"), "does-not-exist").status_code == 404
