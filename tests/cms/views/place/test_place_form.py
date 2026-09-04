from __future__ import annotations

import json
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
    Contact,
    Event,
    Language,
    Place,
    PlaceCategory,
    PlaceTranslation,
    Region,
)
from integreat_cms.cms.models.places.place import get_default_opening_hours
from tests.cms.views.bulk_actions import assert_bulk_delete, BulkActionIDs
from tests.constants import (
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
    barrier_free_box = '<div id="place-barrier-free"'
    organization_box = '<div id="place-organization"'
    client, role = login_role_user

    edit_place = reverse(
        "edit_place",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "place_id": 1},
    )
    response = client.get(edit_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_place}"
        )
        return

    assert organization_box in response.content.decode("utf-8")
    assert barrier_free_box in response.content.decode("utf-8")


# Choose a region
REGION_SLUG = "augsburg"


def create_place_used_by_event(region_slug: str, name_add: str = "") -> int:
    """
    A helper function to create a new Place used in an event
    """
    region = Region.objects.filter(slug=region_slug).first()
    event = Event.objects.filter(region=region).first()
    place_category = PlaceCategory.objects.first()

    used_place = Place.objects.create(
        region_id=region.id,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )

    german_language = Language.objects.filter(slug="de").first()
    PlaceTranslation.objects.create(
        title="Ort" + name_add,
        slug="ort" + name_add,
        status=status.PUBLIC,
        content="",
        language=german_language,
        place=used_place,
    )

    event.place = used_place
    event.save()

    assert used_place.events.count() > 0

    return used_place.id


def create_place_used_by_contact(region_slug: str, name_add: str = "") -> int:
    """
    helper function to create a new Place that is used in a contact
    """
    region = Region.objects.filter(slug=region_slug).first()
    contact = Contact.objects.filter(place__region=region).first()
    place_category = PlaceCategory.objects.first()

    used_place = Place.objects.create(
        region_id=region.id,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )

    german_language = Language.objects.filter(slug="de").first()
    PlaceTranslation.objects.create(
        title="Ort" + name_add,
        slug="ort" + name_add,
        status=status.PUBLIC,
        content="",
        language=german_language,
        place=used_place,
    )

    contact.place = used_place
    contact.save()

    assert used_place.contacts.count() > 0

    return used_place.id


def create_not_currently_used_place(region_slug: str) -> int:
    """
    A helper function to create a new Place that is used in an event that is already past
    """
    region = Region.objects.filter(slug=region_slug).first()
    event = Event.objects.create(
        start=timezone.now() - timedelta(days=2),
        end=timezone.now() - timedelta(days=1),
        region=region,
    )
    place_category = PlaceCategory.objects.first()

    used_place = Place.objects.create(
        region_id=region.id,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )

    german_language = Language.objects.filter(slug="de").first()
    PlaceTranslation.objects.create(
        title="Ort",
        slug="ort",
        status=status.PUBLIC,
        content="",
        language=german_language,
        place=used_place,
    )

    event.place = used_place
    event.save()

    assert used_place.events.count() > 0

    return used_place.id


def create_unused_place(region_slug: str, name_add: str = "") -> int:
    """
    A helper function to create a new Place that is unused (and therefore deletable)
    """
    region = Region.objects.filter(slug=region_slug).first()
    place_category = PlaceCategory.objects.first()

    unused_place = Place.objects.create(
        region_id=region.id,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )

    german_language = Language.objects.filter(slug="de").first()
    PlaceTranslation.objects.create(
        title="Ort" + name_add,
        slug="ort" + name_add,
        status=status.PUBLIC,
        content="",
        language=german_language,
        place=unused_place,
    )

    assert unused_place.events.count() == 0

    return unused_place.id


@pytest.mark.django_db
def test_place_currently_used_by_event_cannot_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place is protected from archiving if it is currently used in an event
    but can be archived if referencing events are archived
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target Place is used in an event
    place_id = create_place_used_by_event("augsburg")

    # Try to archive the Place
    archive_place = reverse(
        "archive_place",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "place_id": place_id},
    )
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            "ERROR    This place cannot be archived because it is referenced by an event or a contact that is not archived.",
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the Place is not archived
    assert not Place.objects.filter(id=place_id).first().archived

    # Archive referencing events
    for event in Place.objects.filter(id=place_id).first().events.all():
        event.archived = True
        event.save()

    # Try to archive the Place
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            "SUCCESS  Place was successfully archived",
            caplog,
        )
        # Check the Place is archived
        assert Place.objects.filter(id=place_id).first().archived
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_place_currently_used_by_contact_cannot_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place is protected from archiving if it is currently used in a contact
    but can be archived if referencing contacts are archived
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target Place is used in a contact
    place_id = create_place_used_by_contact("augsburg")

    # Try to archive the Place
    archive_place = reverse(
        "archive_place",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "place_id": place_id},
    )
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            "ERROR    This place cannot be archived because it is referenced by an event or a contact that is not archived.",
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the Place is not archived
    assert not Place.objects.filter(id=place_id).first().archived

    # Archive referencing contacts
    for contact in Place.objects.filter(id=place_id).first().contacts.all():
        contact.archived = True
        contact.save()

    # Try to archive the Place
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            "SUCCESS  Place was successfully archived",
            caplog,
        )
        # Check the Place is archived
        assert Place.objects.filter(id=place_id).first().archived
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_place_used_by_past_event_can_be_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place can be arhcived if it is used by a past event
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target Place is used in a past event only
    place_id = create_not_currently_used_place("augsburg")

    # Try to archive the Place
    archive_place = reverse(
        "archive_place",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "place_id": place_id},
    )
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log("SUCCESS  Place was successfully archived", caplog)
        # Check the Place is archived
        assert Place.objects.get(id=place_id).archived
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_place_archive_not_crash(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place can be archived successfully in a region that does not use contact feature (regression found in #4436)
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    place_id = create_place_used_by_contact("augsburg")

    region = Region.objects.filter(slug="augsburg").first()
    region.contacts_enabled = False
    region.save()

    archive_place = reverse(
        "archive_place",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
            "place_id": place_id,
        },
    )
    response = client.post(archive_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_place}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log("SUCCESS  Place was successfully archived", caplog)
        # Check the Place is archived
        assert Place.objects.get(id=place_id).archived
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_place_in_use_not_deleted(
    load_test_data: None,
    caplog: LogCaptureFixture,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place is protected from deleting if it is used in an event
    """
    client, role = login_role_user

    settings.LANGUAGE_CODE = "en"

    # Make sure the target Place is used in an event
    place_id = create_place_used_by_event("augsburg")

    # Try to delete the Place
    delete_place = reverse(
        "delete_place",
        kwargs={"region_slug": "augsburg", "language_slug": "en", "place_id": place_id},
    )

    if role == ANONYMOUS:
        response = client.post(delete_place)
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_place}"
        )
    elif role in HIGH_PRIV_STAFF_ROLES:
        client.post(delete_place)
        assert_message_in_log(
            "ERROR    Place couldn't be deleted, because a place used by an event or a contact cannot be deleted.",
            caplog,
        )
    else:
        response = client.post(delete_place)
        assert response.status_code == 403

    # Check the Place still exists
    assert Place.objects.filter(id=place_id).first()


@pytest.mark.django_db
def test_place_in_use_not_bulk_archived(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    """
    Checks whether a Place is protected from bulk archiving if it is used in an event
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    # Make sure the target Place is used in an event
    place_id = create_place_used_by_event("augsburg")

    # Try to archive the Place by bulk action
    bulk_archive_places = reverse(
        "bulk_archive_places",
        kwargs={"region_slug": "augsburg", "language_slug": "de"},
    )
    response = client.post(bulk_archive_places, data={"selected_ids[]": [place_id]})

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_archive_places}"
        )
    elif role in PRIV_STAFF_ROLES + WRITE_ROLES:
        assert_message_in_log(
            'ERROR    Place "Ort" could not be archived because it is referenced by an event or a contact.',
            caplog,
        )
    else:
        assert response.status_code == 403

    # Check the Place is not archived
    assert not Place.objects.filter(id=place_id).first().archived


@pytest.mark.django_db
def test_place_form_shows_associated_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Place "Draft location" (id=6) has four related contacts. Test whether they are shown in the Place form.
    """
    client, role = login_role_user

    # Choose a Place which has related contacts
    PLACE_ID = 6

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    place = Place.objects.filter(id=PLACE_ID).first()
    related_contacts = list(place.contacts.all())

    assert len(related_contacts) > 0

    edit_place = reverse(
        "edit_place",
        kwargs={
            "place_id": place.id,
            "region_slug": place.region.slug,
            "language_slug": place.region.default_language.slug,
        },
    )
    response = client.get(edit_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_place}"
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
            "This place is currently referred to in those contacts."
            not in response.content.decode("utf-8")
        )


@pytest.mark.django_db
def test_place_form_shows_no_associated_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Place "Test location" (id=4) has no related contacts. Test whether the correct message is shown in the Place form.
    """
    client, role = login_role_user

    # Choose a Place which has related contacts
    PLACE_ID = 4

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    place = Place.objects.filter(id=PLACE_ID).first()
    related_contacts = list(place.contacts.all())

    assert len(related_contacts) == 0

    edit_place = reverse(
        "edit_place",
        kwargs={
            "place_id": place.id,
            "region_slug": place.region.slug,
            "language_slug": place.region.default_language.slug,
        },
    )
    response = client.get(edit_place)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_place}"
        )
    if role in (*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert (
            "This place is not currently referred to in any contact."
            in response.content.decode("utf-8")
        )
    else:
        assert (
            "This place is not currently referred to in any contact."
            not in response.content.decode("utf-8")
        )


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ROOT", "AUTHOR"])
@pytest.mark.parametrize(
    "num_deletable, num_undeletable",
    [
        pytest.param(1, 1, id="deletable_place=1_undeletable_place=1"),
        pytest.param(2, 0, id="deletable_places=2"),
        pytest.param(0, 2, id="undeletable_places=2"),
        pytest.param(2, 2, id="deletable_places=2_undeletable_places=2"),
    ],
)
def test_bulk_delete_places(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_deletable: int,
    num_undeletable: int,
) -> None:
    """
    Test whether bulk deleting of places works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    deletable_places = [
        create_unused_place("augsburg", f"-{i}") for i in range(num_deletable)
    ]
    undeletable_places = [
        create_place_used_by_event("augsburg", f"-{i}-used")
        for i in range(num_undeletable)
    ]
    instance_ids: BulkActionIDs = {
        "deletable": deletable_places,
        "undeletable": [undeletable_places],
    }
    fail_reason = "a place used by an event or a contact cannot be deleted."
    url = reverse(
        "bulk_delete_places",
        kwargs={"region_slug": "augsburg", "language_slug": "en"},
    )
    assert_bulk_delete(
        Place, instance_ids, url, (client, role), caplog, settings, [fail_reason]
    )


@pytest.mark.django_db
def test_case_insensitive_unique_slug(
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
) -> None:
    """
    Test that an appropriate message is shown to users and the view does not crash when slug is updated for uniqueness
    """
    settings.LANGUAGE_CODE = "en"

    region = Region.objects.get(slug="augsburg")
    language = Language.objects.get(slug="de")

    place_category = PlaceCategory.objects.first()
    place = Place.objects.create(
        region=region,
        address="Test Street 1",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=place_category,
    )
    PlaceTranslation.objects.create(place=place, language=language, slug="slug")

    assert PlaceTranslation.objects.filter(slug="slug").count() == 1
    assert PlaceTranslation.objects.filter(slug="slug-2").count() == 0

    user = get_user_model().objects.get(username="service_team")
    client.force_login(user)

    new_event_url = reverse(
        "new_place",
        kwargs={
            "region_slug": region.slug,
            "language_slug": language.slug,
        },
    )

    response = client.post(
        new_event_url,
        data={
            "content": "",
            "title": "Slug",
            "slug": "Slug",
            "address": "Viktoriastraße 1",
            "postcode": "86150",
            "city": "Augsburg",
            "country": "Deutschland",
            "latitude": 48.36599805,
            "longitude": 10.886110466584793,
            "status": status.DRAFT,
            "category": place_category.id,
            "opening_hours": json.dumps(get_default_opening_hours()),
            "primary_email": "",
            "primary_website": "",
            "primary_phone_number": "",
        },
    )

    assert response.status_code == 302

    redirect_url = response.headers.get("location")

    assert (
        "The slug was changed from &#x27;Slug&#x27; to &#x27;slug-2&#x27;."
        in client.get(redirect_url).content.decode("utf-8")
    )

    assert PlaceTranslation.objects.filter(slug="slug").count() == 1
    assert PlaceTranslation.objects.filter(slug="slug-2").count() == 1
