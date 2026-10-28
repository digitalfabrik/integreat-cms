from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch

import cacheops.conf
import pytest
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.signals import setting_changed
from django.db import OperationalError
from django.db.models.signals import post_save
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.api.v3.region_statistics import (
    Condition,
    Statistics,
    transform_region_condition,
)
from integreat_cms.cms.constants import region_status
from integreat_cms.cms.models import ApiToken, Region, RegionCondition
from integreat_cms.cms.utils import region_condition_utils
from integreat_cms.cms.utils.region_condition_utils import (
    cacheops_disabled,
    compute_region_condition,
    COMPUTED_STATUSES,
    update_region_conditions,
)
from integreat_cms.cms.views.region_condition.region_condition_actions import (
    RegionConditionResource,
)
from integreat_cms.integreat_celery import celery

#: Values the test data cannot produce, so a response containing them must come from the database.
#: They are pairwise distinct, so every metric can be traced to its key in the API.
STORED_VALUES = {
    "num_broken_links": 4321,
    "num_low_hix_pages": 1234,
    "num_pages": 98765,
    "num_pages_with_missing_or_outdated_translation": 555,
    "num_outdated_pages": 666,
    "num_languages_besides_root_language": 77,
}

#: The same values as returned by the API
STORED_CONDITION = {
    "num_broken_links": 4321,
    "num_low_hix_page_translations": 1234,
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


def _store(
    region_slug: str = "augsburg",
    computed_at: datetime = STORED_AT,
    **values: int,
) -> RegionCondition:
    """
    Store a condition with recognizable values for a region

    :param region_slug: The slug of the region
    :param computed_at: The time the values were computed
    :param \\**values: Metric values which differ from :data:`STORED_VALUES`
    :return: The stored condition
    """
    return RegionCondition.objects.create(
        region=Region.objects.get(slug=region_slug),
        computed_at=computed_at,
        **{**STORED_VALUES, **values},
    )


def _computed_slugs() -> list[str]:
    """
    :return: The slugs of all regions whose condition is computed, in the order of their slugs
    """
    return list(
        Region.objects.filter(status__in=COMPUTED_STATUSES)
        .order_by("slug")
        .values_list("slug", flat=True),
    )


@pytest.mark.django_db
def test_metrics_match_the_model_and_the_api(load_test_data: None) -> None:
    """
    Every metric field of the model is computed by the export and exposed by the API.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    model_fields = {field.name for field in RegionCondition._meta.concrete_fields}
    assert set(RegionCondition.METRICS) == model_fields - {
        "id",
        "region",
        "computed_at",
    }
    assert all(
        hasattr(RegionConditionResource, f"dehydrate_{metric}")
        for metric in RegionCondition.METRICS
    )
    # The stored values are pairwise distinct, so this proves each metric reaches its own key
    condition = transform_region_condition(_store())
    assert set(condition) == set(Condition.__annotations__)
    assert sorted(v for k, v in condition.items() if k != "computed_at") == sorted(
        STORED_VALUES.values(),
    )


@pytest.mark.django_db
def test_statistics_before_first_computation(load_test_data: None) -> None:
    """
    As long as nothing is stored, ``condition`` is ``None`` instead of being computed on request.
    The budget is read live and its three values are distinguishable.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    region = Region.objects.get(slug="augsburg")
    region.mt_budget_used = region.mt_budget // 2
    region.save()

    response = _get_statistics(_token_for("root"))

    assert response.status_code == 200
    data = response.json()
    assert set(data) == set(Statistics.__annotations__)
    assert data["condition"] is None
    assert data["mt_budget"] == region.mt_budget
    assert data["mt_budget_used"] == region.mt_budget // 2
    assert data["mt_budget_remaining"] == region.mt_budget - region.mt_budget // 2


@pytest.mark.django_db
def test_statistics_return_the_stored_values_of_the_region(
    load_test_data: None,
) -> None:
    """
    The endpoint returns exactly what is stored for the requested region.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    _store("nurnberg", num_pages=11111)
    token = _token_for("root")

    assert _get_statistics(token, "augsburg").json()["condition"] is None

    _store("augsburg")
    assert _get_statistics(token, "augsburg").json()["condition"] == {
        "computed_at": STORED_AT.isoformat(),
        **STORED_CONDITION,
    }
    assert _get_statistics(token, "nurnberg").json()["condition"]["num_pages"] == 11111


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

    result = update_region_conditions()

    assert result.failed == []
    assert result.not_reached == []
    assert result.updated == len(_computed_slugs())
    assert (
        sorted(
            RegionCondition.objects.values_list("region__slug", flat=True),
        )
        == _computed_slugs()
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
def test_regions_without_or_with_oldest_values_come_first(load_test_data: None) -> None:
    """
    A run that is cut short must not always miss the same regions.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    slugs = _computed_slugs()
    # The first region gets the newest values, the second the oldest, the rest none at all
    _store(slugs[0], computed_at=STORED_AT + timedelta(days=2))
    _store(slugs[1], computed_at=STORED_AT)
    order: list[str] = []
    original = region_condition_utils.compute_region_condition

    def record(region: Region) -> dict[str, int]:
        order.append(region.slug)
        return original(region)

    with patch.object(
        region_condition_utils,
        "compute_region_condition",
        side_effect=record,
    ):
        update_region_conditions()

    assert order == [*slugs[2:], slugs[1], slugs[0]]


@pytest.mark.django_db
def test_failing_region_keeps_its_values_and_does_not_stop_the_others(
    load_test_data: None,
) -> None:
    """
    One broken region is reported and keeps its last values; the regions after it are updated.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    # Give every other region newer values, so the failing one is computed first
    for slug in _computed_slugs():
        if slug != "augsburg":
            _store(slug, computed_at=STORED_AT + timedelta(days=1))
    _store("augsburg")
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
        result = update_region_conditions()

    assert result.failed == ["augsburg"]
    assert result.updated == len(_computed_slugs()) - 1
    condition = RegionCondition.objects.get(region__slug="augsburg")
    assert condition.computed_at == STORED_AT
    assert condition.num_pages == STORED_VALUES["num_pages"]
    assert all(
        computed_at > STORED_AT + timedelta(days=1)
        for computed_at in RegionCondition.objects.exclude(
            region__slug="augsburg",
        ).values_list("computed_at", flat=True)
    )


@pytest.mark.django_db
def test_region_archived_during_the_run_is_not_stored(load_test_data: None) -> None:
    """
    A region archived while the run is computing it must not get a fresh row.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    original = region_condition_utils.compute_region_condition

    def archive_augsburg(region: Region) -> dict[str, int]:
        metrics = original(region)
        if region.slug == "augsburg":
            Region.objects.filter(pk=region.pk).update(status=region_status.ARCHIVED)
        return metrics

    with patch.object(
        region_condition_utils,
        "compute_region_condition",
        side_effect=archive_augsburg,
    ):
        result = update_region_conditions()

    assert result.failed == []
    assert not RegionCondition.objects.filter(region__slug="augsburg").exists()


@pytest.mark.django_db
def test_time_budget_stops_starting_new_regions(load_test_data: None) -> None:
    """
    Once the budget is used up, no further region is started and the rest are reported.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    result = update_region_conditions(time_budget=-1)

    assert result.updated == 0
    assert sorted(result.not_reached) == _computed_slugs()
    assert not RegionCondition.objects.exists()


@pytest.mark.django_db
def test_time_limit_is_propagated_and_logged(
    load_test_data: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    If Celery's time limit hits anyway, the run fails, keeps what it stored and names the rest.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param caplog: The fixture capturing the log output
    """
    slugs = _computed_slugs()
    original = region_condition_utils.compute_region_condition

    def time_out_after_the_first(region: Region) -> dict[str, int]:
        if region.slug != slugs[0]:
            raise SoftTimeLimitExceeded
        return original(region)

    with (
        caplog.at_level(logging.ERROR),
        patch.object(
            region_condition_utils,
            "compute_region_condition",
            side_effect=time_out_after_the_first,
        ),
        pytest.raises(SoftTimeLimitExceeded),
    ):
        update_region_conditions()

    assert RegionCondition.objects.filter(region__slug=slugs[0]).exists()
    message = "\n".join(record.getMessage() for record in caplog.records)
    assert f"not updated: {', '.join(slugs[1:])};" in message


@pytest.mark.django_db
def test_lost_database_connection_aborts_the_run(load_test_data: None) -> None:
    """
    A broken connection is not a problem of one region and must not be reported once per region.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with (
        patch.object(
            region_condition_utils,
            "compute_region_condition",
            side_effect=OperationalError("connection lost"),
        ) as compute,
        pytest.raises(OperationalError),
    ):
        update_region_conditions()

    compute.assert_called_once()


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


def test_cacheops_is_restored_even_if_the_restore_is_interrupted() -> None:
    """
    A stale memoized ``CACHEOPS_ENABLED`` must not outlive the block, even if the
    ``setting_changed`` signal of the restore never reached cacheops.
    """
    with override_settings(CACHEOPS_ENABLED=True):
        with pytest.raises(SoftTimeLimitExceeded), cacheops_disabled():
            assert cacheops.conf.settings.CACHEOPS_ENABLED is False
            # The restore restores Django's settings, then dies before notifying cacheops
            patch.object(
                setting_changed,
                "send_robust",
                side_effect=SoftTimeLimitExceeded,
            ).start()
        patch.stopall()
        assert cacheops.conf.settings.CACHEOPS_ENABLED is True


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


@pytest.mark.django_db
def test_command_names_the_regions_not_reached(load_test_data: None) -> None:
    """
    The management command fails when the time budget left regions out.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with pytest.raises(CommandError, match=r"not reached in time for .*augsburg"):
        call_command("update_region_conditions", time_budget=-1)


def test_celery_task_is_scheduled_routed_and_limited() -> None:
    """
    The nightly task is scheduled, runs the command with a time budget, goes to the statistics
    queue and has a soft limit below the hard one.
    """
    sender = Mock()
    celery.setup_periodic_tasks(sender)
    schedules = {
        call.kwargs["name"]: call.args[0]
        for call in sender.add_periodic_task.call_args_list
    }
    assert schedules["wrapper_update_region_conditions"] == crontab(hour=2, minute=30)

    route = celery.app.amqp.router.route(
        {},
        celery.wrapper_update_region_conditions.name,
    )
    assert route["queue"].name == "statistics"

    task = celery.wrapper_update_region_conditions
    assert 0 < task.soft_time_limit < settings.CELERY_TASK_TIME_LIMIT

    with patch.object(celery, "call_command") as call:
        task()
    call.assert_called_once()
    assert call.call_args.args == ("update_region_conditions",)
    assert 0 < call.call_args.kwargs["time_budget"] < task.soft_time_limit


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
