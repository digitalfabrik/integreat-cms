from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Contact, Region
from tests.conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES
from tests.utils import assert_message_in_log

# Use the region Augsburg, as it has some contacts in the test data
REGION_SLUG = "augsburg"
# Use the location with id=6, as it is used by the contacts of Augsburg and has already a primary contact.
POI_ID = 6


@pytest.mark.django_db
def test_create_a_new_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that a new contact is created successfully when all the necessary input are given.
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    new_contact = reverse(
        "new_contact",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_contact,
        data={
            "location": POI_ID,
            "point_of_contact_for": "Title",
            "name": "Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert_message_in_log(
            'SUCCESS  Contact for "Draft location with point of contact for: Title" was successfully created',
            caplog,
        )
        edit_url = response.headers.get("location")
        response = client.get(edit_url)
        assert (
            "Contact for &quot;Draft location with point of contact for: Title&quot; was successfully created"
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_contact}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_edit_a_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that a contact is changed successfully when all the necessary input are given.
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    region = Region.objects.filter(slug=REGION_SLUG).first()
    contact_id = Contact.objects.filter(location__region=region).first().id

    edit_contact = reverse(
        "edit_contact",
        kwargs={
            "region_slug": REGION_SLUG,
            "contact_id": contact_id,
        },
    )
    response = client.post(
        edit_contact,
        data={
            "location": POI_ID,
            "point_of_contact_for": "Title Updated",
            "name": "New Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert_message_in_log(
            'SUCCESS  Contact for "Draft location with point of contact for: Title Updated" was successfully saved',
            caplog,
        )
        edit_url = response.headers.get("location")
        response = client.get(edit_url)
        assert (
            "Contact for &quot;Draft location with point of contact for: Title Updated&quot; was successfully saved"
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_contact}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_no_contact_without_poi(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that a new contact cannot be created without any POI selected.
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    new_contact = reverse(
        "new_contact",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_contact,
        data={
            "point_of_contact_for": "Title",
            "name": "Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert_message_in_log(
            "ERROR    Location: This field is required.",
            caplog,
        )
        assert "Location: This field is required." in response.content.decode("utf-8")

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_contact}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_at_least_one_field_filled(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that a new contact cannot be created when all the fields are left empty.
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    new_contact = reverse(
        "new_contact",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_contact,
        data={
            "location": POI_ID,
            "point_of_contact_for": "",
            "name": "",
            "email": "",
            "phone_number": "",
            "website": "",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert_message_in_log(
            "ERROR    One of the following fields must be filled: point of contact for, name, e-mail, phone number, website.",
            caplog,
        )
        assert (
            "One of the following fields must be filled: point of contact for, name, e-mail, phone number, website."
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_contact}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_one_primary_contact_per_poi(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test that for each POI no second contact without title and name can be created.
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    new_contact = reverse(
        "new_contact",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_contact,
        data={
            "location": POI_ID,
            "point_of_contact_for": "",
            "name": "",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert_message_in_log(
            "ERROR    Only one contact per location can have an empty point of contact.",
            caplog,
        )
        assert (
            "Only one contact per location can have an empty point of contact."
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_contact}"
        )
    else:
        assert response.status_code == 403
