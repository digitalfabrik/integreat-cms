from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.models import Region
from tests.constants import ANONYMOUS, PRIV_STAFF_ROLES

if TYPE_CHECKING:
    from django.test.client import Client

REGION_SLUG = "augsburg"


def mark_as_api_managed(slug: str = REGION_SLUG) -> Region:
    """
    Mark a region as managed by an external system via the API

    :param slug: The slug of the region
    :return: The region
    """
    region = Region.objects.get(slug=slug)
    region.api_settings_synced_at = timezone.now()
    region.save(update_fields=["api_settings_synced_at"])
    return region


@pytest.mark.django_db
def test_release_api_management(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Test that only privileged staff can release a region from API management

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role
    """
    client, role = login_role_user
    region = mark_as_api_managed()
    assert region.is_api_managed

    url = reverse("release_api_management", kwargs={"slug": REGION_SLUG})
    response = client.post(url)

    region.refresh_from_db()
    if role in PRIV_STAFF_ROLES:
        assert response.status_code == 302
        assert response.headers.get("location") == reverse(
            "edit_region",
            kwargs={"slug": REGION_SLUG},
        )
        assert region.api_settings_synced_at is None
        assert not region.is_api_managed
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
        assert region.is_api_managed
    else:
        assert response.status_code == 403
        assert region.is_api_managed


@pytest.mark.django_db
def test_release_keeps_the_synced_settings(
    load_test_data: None,
    admin_client: Client,
) -> None:
    """
    Test that releasing a region only lifts the lock and does not reset any setting

    The values the external system pushed last stay in place -- the release states who maintains
    them from now on, not what they should be.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client of the superuser
    """
    region = mark_as_api_managed()
    region.mt_budget_booked = 123456
    region.mt_renewal_month = 7
    region.events_enabled = False
    region.save(
        update_fields=["mt_budget_booked", "mt_renewal_month", "events_enabled"],
    )

    admin_client.post(
        reverse("release_api_management", kwargs={"slug": REGION_SLUG}),
    )

    region.refresh_from_db()
    assert region.api_settings_synced_at is None
    assert region.mt_budget_booked == 123456
    assert region.mt_renewal_month == 7
    assert region.events_enabled is False


@pytest.mark.django_db
def test_release_of_a_region_which_is_not_api_managed(
    load_test_data: None,
    admin_client: Client,
) -> None:
    """
    Test that releasing a region which is not API-managed is a no-op with a hint

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client of the superuser
    """
    region = Region.objects.get(slug=REGION_SLUG)
    assert not region.is_api_managed

    response = admin_client.post(
        reverse("release_api_management", kwargs={"slug": REGION_SLUG}),
        follow=True,
    )

    assert response.status_code == 200
    region.refresh_from_db()
    assert not region.is_api_managed
    # The message level is asserted instead of its text, which is translated: a hint, not a
    # success -- nothing was released, so claiming otherwise would be misleading.
    emitted = list(response.context["messages"])
    assert len(emitted) == 1
    assert emitted[0].level_tag == "info"


@pytest.mark.django_db
def test_release_requires_post(
    load_test_data: None,
    admin_client: Client,
) -> None:
    """
    Test that the release cannot be triggered by a GET request

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the http client of the superuser
    """
    region = mark_as_api_managed()

    response = admin_client.get(
        reverse("release_api_management", kwargs={"slug": REGION_SLUG}),
    )

    assert response.status_code == 405
    region.refresh_from_db()
    assert region.is_api_managed
