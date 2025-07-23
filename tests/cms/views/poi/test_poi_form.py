from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import (
    Event,
    Language,
    POI,
    POICategory,
    POITranslation,
    Region,
)
from tests.cms.views.bulk_actions import assert_bulk_delete, BulkActionIDs
from tests.conftest import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
    PRIV_STAFF_ROLES,
    STAFF_ROLES,
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


def create_used_poi(region_slug: str, name_add: str = "") -> int:
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
        title="Ort" + name_add,
        slug="ort" + name_add,
        status=status.PUBLIC,
        content="",
        language=german_language,
        poi=used_poi,
    )

    event.location = used_poi
    event.save()

    assert used_poi.events.count() > 0

    return used_poi.id


def create_not_currently_used_poi(region_slug: str) -> int:
    """
    A helper function to create a new POI that is used in an event that is already past
    """
    region = Region.objects.filter(slug=region_slug).first()
    event = Event.objects.create(
        start=timezone.now() - timedelta(days=2),
        end=timezone.now() - timedelta(days=1),
        region=region,
    )
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


def create_unused_poi(region_slug: str, name_add: str = "") -> int:
    """
    A helper function to create a new POI that is unused (and therefore deletable)
    """
    region = Region.objects.filter(slug=region_slug).first()
    poi_category = POICategory.objects.first()

    unused_poi = POI.objects.create(
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
        title="Ort" + name_add,
        slug="ort" + name_add,
        status=status.PUBLIC,
        content="",
        language=german_language,
        poi=unused_poi,
    )

    assert unused_poi.events.count() == 0

    return unused_poi.id


@pytest.mark.django_db
def test_poi_currently_in_use_cannot_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a POI is protected from archiving if it is currently used in an event
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
def test_poi_used_by_past_event_can_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a POI can be arhcived if it is used by a past event
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target POI is used in a past event only
    poi_id = create_not_currently_used_poi("augsburg")

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
        assert_message_in_log("SUCCESS  Location was successfully archived", caplog)
        # Check the POI is archived
        assert POI.objects.get(id=poi_id).archived
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_poi_in_use_not_deleted(
    load_test_data: None,
    caplog: LogCaptureFixture,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a POI is protected from deleting if it is used in an event
    """
    client, role = login_role_user

    settings.LANGUAGE_CODE = "en"

    # Make sure the target POI is used in an event
    poi_id = create_used_poi("augsburg")

    # Try to delete the POI
    delete_poi = reverse(
        "delete_poi",
        kwargs={"region_slug": "augsburg", "language_slug": "en", "poi_id": poi_id},
    )

    if role == ANONYMOUS:
        response = client.post(delete_poi)
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_poi}"
        )
    elif role in HIGH_PRIV_STAFF_ROLES:
        client.post(delete_poi)
        assert_message_in_log(
            "ERROR    Location couldn't be deleted, because a poi used by an event or a contact cannot be deleted.",
            caplog,
        )
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
        "bulk_archive_pois",
        kwargs={"region_slug": "augsburg", "language_slug": "de"},
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
            'ERROR    Location "Ort" could not be archived because it is referenced by an event or a contact.',
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the POI is not archived
    assert not POI.objects.filter(id=poi_id).first().archived


@pytest.mark.django_db
def test_poi_form_shows_associated_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    POI "Draft location" (id=6) has four related contacts. Test whether they are shown in the POI form.
    """
    client, role = login_role_user

    # Choose a POI which has related contacts
    POI_ID = 6

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    poi = POI.objects.filter(id=POI_ID).first()
    related_contacts = list(poi.contacts.all())

    assert len(related_contacts) > 0

    edit_poi = reverse(
        "edit_poi",
        kwargs={
            "poi_id": poi.id,
            "region_slug": poi.region.slug,
            "language_slug": poi.region.default_language.slug,
        },
    )
    response = client.get(edit_poi)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={edit_poi}"
        )
    # probably needs adjustment after #2958
    elif role in HIGH_PRIV_STAFF_ROLES:
        for contact in related_contacts:
            if contact.area_of_responsibility:
                assert (
                    f"{contact.area_of_responsibility} {contact.name}"
                    in response.content.decode("utf-8")
                )
            else:
                assert "General contact information" in response.content.decode("utf-8")
    else:
        assert (
            "This location is currently referred to in those contacts."
            not in response.content.decode("utf-8")
        )


@pytest.mark.django_db
def test_poi_form_shows_no_associated_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    POI "Test location" (id=4) has no related contacts. Test whether the correct message is shown in the POi form.
    """
    client, role = login_role_user

    # Choose a POI which has related contacts
    POI_ID = 4

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    poi = POI.objects.filter(id=POI_ID).first()
    related_contacts = list(poi.contacts.all())

    assert len(related_contacts) == 0

    edit_poi = reverse(
        "edit_poi",
        kwargs={
            "poi_id": poi.id,
            "region_slug": poi.region.slug,
            "language_slug": poi.region.default_language.slug,
        },
    )
    response = client.get(edit_poi)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={edit_poi}"
        )
    if role in (*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert (
            "This location is not currently referred to in any contact."
            in response.content.decode("utf-8")
        )
    else:
        assert (
            "This location is not currently referred to in any contact."
            not in response.content.decode("utf-8")
        )


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ROOT", "AUTHOR"])
@pytest.mark.parametrize(
    "num_deletable, num_undeletable",
    [
        pytest.param(1, 1, id="deletable_poi=1_undeletable_poi=1"),
        pytest.param(2, 0, id="deletable_pois=2"),
        pytest.param(0, 2, id="undeletable_pois=2"),
        pytest.param(2, 2, id="deletable_pois=2_undeletable_pois=2"),
    ],
)
def test_bulk_delete_pois(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_deletable: int,
    num_undeletable: int,
) -> None:
    """
    Test whether bulk deleting of pois works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    deletable_pois = [
        create_unused_poi("augsburg", f"-{i}") for i in range(num_deletable)
    ]
    undeletable_pois = [
        create_used_poi("augsburg", f"-{i}-used") for i in range(num_undeletable)
    ]
    instance_ids: BulkActionIDs = {
        "deletable": deletable_pois,
        "undeletable": [undeletable_pois],
    }
    fail_reason = "a poi used by an event or a contact cannot be deleted."
    url = reverse(
        "bulk_delete_pois",
        kwargs={"region_slug": "augsburg", "language_slug": "en"},
    )
    assert_bulk_delete(
        POI, instance_ids, url, (client, role), caplog, settings, [fail_reason]
    )
