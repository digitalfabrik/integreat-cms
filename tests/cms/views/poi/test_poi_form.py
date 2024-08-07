from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

from django.conf import settings
from django.db.models import ProtectedError
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import (
    Event,
    Language,
    POI,
    POICategory,
    POITranslation,
    Region,
)
from tests.conftest import (
    ANONYMOUS,
    HIGH_PRIV_STAFF_ROLES,
    PRIV_STAFF_ROLES,
    WRITE_ROLES,
)
from tests.utils import assert_message_in_log


@pytest.mark.django_db
def test_barrier_free_and_organization_box_appear(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    barrier_free_box = '<div id="poi-barrier-free"'
    organization_box = '<div id="poi-organization"'
    client, role = login_role_user

    edit_poi = reverse(
        "edit_poi",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "poi_id": 1},
    )
    response = client.get(edit_poi)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={edit_poi}"
        )
        return

    assert organization_box in response.content.decode("utf-8")
    assert barrier_free_box in response.content.decode("utf-8")


# Choose a region
REGION_SLUG = "augsburg"


def create_used_poi(region_slug: str) -> int:
    """
    A helper function to create a new POI used in an event
    """
    region = Region.objects.filter(slug=region_slug).first()
    event = Event.objects.filter(region=region).first()
    poi_category = POICategory.objects.first()

    used_poi = POI.objects.create(
        region_id=region.id,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )

    german_language = Language.objects.filter(slug="de").first()
    POITranslation.objects.create(
        title="Ort",
        slug="ort",
        status=status.PUBLIC,
        content="",
        language=german_language,
        poi=used_poi,
    )

    event.location = used_poi
    event.save()

    assert used_poi.events.count() > 0

    return used_poi.id


@pytest.mark.django_db
def test_poi_in_use_cannot_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a POI is protected from archiving if it is used in an event
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target POI is used in an event
    poi_id = create_used_poi("augsburg")

    # Try to archive the POI
    archive_poi = reverse(
        "archive_poi",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "poi_id": poi_id},
    )
    response = client.post(archive_poi)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_poi}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            "ERROR    This location cannot be archived because it is referenced by an event.",
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the POI is not archived
    assert not POI.objects.filter(id=poi_id).first().archived


@pytest.mark.django_db
def test_poi_in_use_not_deleted(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Checks whether a POI is protected from deleting if it is used in an event
    """
    client, role = login_role_user

    # Make sure the target POI is used in an event
    poi_id = create_used_poi("augsburg")

    # Try to delete the POI
    delete_poi = reverse(
        "delete_poi",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "poi_id": poi_id},
    )

    if role == ANONYMOUS:
        response = client.post(delete_poi)
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_poi}"
        )
    elif role in HIGH_PRIV_STAFF_ROLES:
        with pytest.raises(ProtectedError):
            response = client.post(delete_poi)
    else:
        response = client.post(delete_poi)
        assert response.status_code == 403

    # Check the POI still exists
    assert POI.objects.filter(id=poi_id).first()


@pytest.mark.django_db
def test_poi_in_use_not_bulk_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a POI is protected from bulk archiving if it is used in an event
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target POI is used in an event
    poi_id = create_used_poi("augsburg")

    # Try to archive the POI by bulk action
    bulk_archive_pois = reverse(
        "bulk_archive_pois", kwargs={"region_slug": "augsburg", "language_slug": "de"}
    )
    response = client.post(bulk_archive_pois, data={"selected_ids[]": [poi_id]})

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_archive_pois}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            'ERROR    Location "Ort" could not be archived because it is referenced by an event.',
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the POI is not archived
    assert not POI.objects.filter(id=poi_id).first().archived
