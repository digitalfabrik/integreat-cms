from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import Mock, patch

import cacheops.conf
import pytest
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.signals import post_save
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.api.v3.region_statistics import Condition, Statistics
from integreat_cms.cms.constants import region_status
from integreat_cms.cms.models import ApiToken, Region, RegionCondition
from integreat_cms.cms.utils import region_condition_utils
from integreat_cms.cms.utils.region_condition_utils import (
    compute_region_condition,
    update_region_conditions,
)
from integreat_cms.cms.views.region_condition.region_condition_actions import (
    RegionConditionResource,
)
from integreat_cms.integreat_celery import celery

#: Values the test data cannot produce, so a response containing them must come from the database
STORED_VALUES = {
    "num_broken_links": 4321,
    "num_low_hix_pages": 1234,
    "num_pages": 98765,
    "num_pages_with_missing_or_outdated_translation": 555,
    "num_outdated_pages": 666,
    "num_languages_besides_root_language": 77,
}

STORED_AT = datetime(2026, 1, 1, 2, 30, tzinfo=UTC)


def _token_for(user: object) -> str:
    """
    Create an API token for the given user

    :param user: The user or the username of the token's user
    :return: The plaintext token
    """
    if isinstance(user, str):
        user = get_user_model().objects.get(username=user)
    _token, plaintext = ApiToken.create_token(user, "test-token")
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


def _store(region_slug: str = "augsburg") -> RegionCondition:
    """
    Store a condition with recognizable values for a region

    :param region_slug: The slug of the region
    :return: The stored condition
    """
    return RegionCondition.objects.create(
        region=Region.objects.get(slug=region_slug),
        computed_at=STORED_AT,
        **STORED_VALUES,
    )


def test_metrics_match_the_model_and_the_api() -> None:
    """
    The metric names exist once on the model; the model fields and the API shape must match them.
    """
    model_fields = {field.name for field in RegionCondition._meta.concrete_fields}
    assert set(RegionCondition.METRICS) == model_fields - {
        "id",
        "region",
        "computed_at",
    }
    assert set(Condition.__annotations__) == {*RegionCondition.METRICS, "computed_at"}
    assert all(
        hasattr(RegionConditionResource, f"dehydrate_{metric}")
        for metric in RegionCondition.METRICS
    )


@pytest.mark.django_db
def test_statistics_before_first_computation(load_test_data: None) -> None:
    """
    As long as nothing is stored, ``condition`` is ``None`` instead of being computed on request.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    response = _get_statistics(_token_for("root"))

    assert response.status_code == 200
    data = response.json()
    assert set(data) == set(Statistics.__annotations__)
    assert data["condition"] is None
    region = Region.objects.get(slug="augsburg")
    assert data["mt_budget"] == region.mt_budget
    assert data["mt_budget_used"] == region.mt_budget_used
    assert data["mt_budget_remaining"] == region.mt_budget_remaining


@pytest.mark.django_db
def test_statistics_return_the_stored_values(load_test_data: None) -> None:
    """
    The endpoint returns exactly what is stored, not freshly computed numbers.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    _store()

    data = _get_statistics(_token_for("root")).json()

    assert data["condition"] == {
        "computed_at": STORED_AT.isoformat(),
        **STORED_VALUES,
    }


@pytest.mark.django_db
def test_statistics_are_not_computed_on_request(load_test_data: None) -> None:
    """
    Reading the statistics must never run the expensive computation.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    _store()
    dehydrate_methods = {
        f"dehydrate_{metric}": Mock(side_effect=AssertionError("computed on request"))
        for metric in RegionCondition.METRICS
    }

    with patch.multiple(RegionConditionResource, **dehydrate_methods):
        response = _get_statistics(_token_for("root"))

    assert response.status_code == 200
    assert not any(method.called for method in dehydrate_methods.values())


@pytest.mark.django_db
def test_update_covers_exactly_the_active_and_hidden_regions(
    load_test_data: None,
) -> None:
    """
    Active and hidden regions are computed; stored values of other regions are removed.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    archived = Region.objects.filter(status=region_status.ARCHIVED).first()
    assert archived, "the test data needs an archived region"
    _store(archived.slug)

    updated, failed = update_region_conditions()

    expected = set(
        Region.objects.filter(
            status__in=[region_status.ACTIVE, region_status.HIDDEN],
        ).values_list("slug", flat=True),
    )
    assert failed == []
    assert updated == len(expected)
    assert (
        set(RegionCondition.objects.values_list("region__slug", flat=True)) == expected
    )


@pytest.mark.django_db
def test_update_overwrites_the_stored_values(load_test_data: None) -> None:
    """
    A later run replaces the row of a region instead of failing on the one-to-one relation.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    _store()
    region = Region.objects.get(slug="augsburg")

    update_region_conditions()

    condition = RegionCondition.objects.get(region=region)
    assert condition.computed_at > STORED_AT
    assert {
        metric: getattr(condition, metric) for metric in RegionCondition.METRICS
    } == compute_region_condition(region)


@pytest.mark.django_db
def test_failing_region_keeps_its_values_and_does_not_stop_the_others(
    load_test_data: None,
) -> None:
    """
    One broken region is reported and keeps its last values; the others are still updated.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    _store()
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

    assert failed == ["augsburg"]
    assert updated > 0
    condition = RegionCondition.objects.get(region__slug="augsburg")
    assert condition.computed_at == STORED_AT
    assert condition.num_pages == STORED_VALUES["num_pages"]
    assert RegionCondition.objects.exclude(region__slug="augsburg").count() == updated


@pytest.mark.django_db
def test_time_limit_is_propagated(load_test_data: None) -> None:
    """
    A run that runs out of time stops and fails instead of swallowing the time limit.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with (
        patch.object(
            region_condition_utils,
            "compute_region_condition",
            side_effect=SoftTimeLimitExceeded(),
        ),
        pytest.raises(SoftTimeLimitExceeded),
    ):
        update_region_conditions()


@pytest.mark.django_db
def test_cacheops_is_off_while_computing_and_on_while_writing(
    load_test_data: None,
) -> None:
    """
    The heavy queries bypass the cache, but the write must not: with cacheops disabled it would
    not invalidate the cached API read either, which would then serve outdated values.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    while_computing: list[bool] = []
    while_writing: list[bool] = []
    original = RegionConditionResource.dehydrate_num_pages

    def record_computation(region: Region) -> int:
        while_computing.append(cacheops.conf.settings.CACHEOPS_ENABLED)
        return original(region)

    def record_write(**kwargs: object) -> None:
        while_writing.append(cacheops.conf.settings.CACHEOPS_ENABLED)

    post_save.connect(record_write, sender=RegionCondition)
    try:
        with (
            override_settings(CACHEOPS_ENABLED=True),
            patch.object(
                RegionConditionResource,
                "dehydrate_num_pages",
                side_effect=record_computation,
            ),
        ):
            update_region_conditions()
            assert cacheops.conf.settings.CACHEOPS_ENABLED is True
    finally:
        post_save.disconnect(record_write, sender=RegionCondition)

    assert while_computing
    assert not any(while_computing)
    assert while_writing
    assert all(while_writing)


@pytest.mark.django_db
def test_command_succeeds(load_test_data: None) -> None:
    """
    The management command stores the conditions and exits successfully.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    call_command("update_region_conditions")

    assert RegionCondition.objects.filter(region__slug="augsburg").exists()


@pytest.mark.django_db
def test_command_names_the_failed_regions(load_test_data: None) -> None:
    """
    The management command fails and names the regions which could not be computed.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with (
        patch.object(
            region_condition_utils,
            "compute_region_condition",
            side_effect=RuntimeError("broken region"),
        ),
        pytest.raises(CommandError, match="augsburg"),
    ):
        call_command("update_region_conditions")


def test_celery_task_is_scheduled_and_routed() -> None:
    """
    The nightly task is scheduled, runs the command and goes to the statistics queue.
    """
    sender = Mock()
    celery.setup_periodic_tasks(sender)
    schedules = {
        call.kwargs["name"]: call.args[0]
        for call in sender.add_periodic_task.call_args_list
    }
    assert schedules["wrapper_update_region_conditions"] == crontab(hour=2, minute=30)

    route = celery.app.amqp.router.route(
        {}, celery.wrapper_update_region_conditions.name
    )
    assert route["queue"].name == "statistics"

    with patch.object(celery, "call_command") as call:
        celery.wrapper_update_region_conditions()
    call.assert_called_once_with("update_region_conditions")


@pytest.mark.django_db
def test_staff_with_view_permission_may_read(load_test_data: None) -> None:
    """
    A non-superuser holding ``cms.view_region`` (a staff role) gets the statistics.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    staff = next(
        (
            user
            for user in get_user_model().objects.filter(
                is_superuser=False,
                is_active=True,
            )
            if user.has_perm("cms.view_region")
        ),
        None,
    )
    assert staff, "the test data needs a staff user with cms.view_region"

    assert _get_statistics(_token_for(staff)).status_code == 200


@pytest.mark.django_db
def test_requires_permission(load_test_data: None) -> None:
    """
    A token of a user without ``cms.view_region`` is rejected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    unprivileged = next(
        (
            user
            for user in get_user_model().objects.filter(
                is_superuser=False,
                is_active=True,
            )
            if not user.has_perm("cms.view_region")
        ),
        None,
    )
    assert unprivileged, "the test data needs a user without cms.view_region"

    assert _get_statistics(_token_for(unprivileged)).status_code == 403


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
