from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.urls import reverse

from integreat_cms.cms.forms import ContactForm
from integreat_cms.cms.models import Contact, Region
from tests.conftest import ANONYMOUS, AUTHOR, EDITOR, MANAGEMENT, PRIV_STAFF_ROLES
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
            "area_of_responsibility": "Title",
            "name": "Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in (*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert_message_in_log(
            'SUCCESS  Contact for "Draft location with area of responsibility: Title" was successfully created',
            caplog,
        )
        edit_url = response.headers.get("location")
        response = client.get(edit_url)
        assert (
            "Contact for &quot;Draft location with area of responsibility: Title&quot; was successfully created"
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
            "area_of_responsibility": "Title Updated",
            "name": "New Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in (*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert_message_in_log(
            'SUCCESS  Contact for "Draft location with area of responsibility: Title Updated" was successfully saved',
            caplog,
        )
        edit_url = response.headers.get("location")
        response = client.get(edit_url)
        assert (
            "Contact for &quot;Draft location with area of responsibility: Title Updated&quot; was successfully saved"
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
            "area_of_responsibility": "Title",
            "name": "Name",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in (*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
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
            "area_of_responsibility": "",
            "name": "",
            "email": "",
            "phone_number": "",
            "mobile_phone_number": "",
            "fax_number": "",
            "website": "",
        },
    )

    if role in (*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert_message_in_log(
            "ERROR    One of the following fields must be filled: area of responsibility, name, e-mail, phone number, mobile phone number, fax number, website.",
            caplog,
        )
        assert (
            "One of the following fields must be filled: area of responsibility, name, e-mail, phone number, mobile phone number, fax number, website."
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
            "area_of_responsibility": "",
            "name": "",
            "email": "mail@mail.integreat",
            "phone_number": "0123456789",
            "website": "https://integreat-app.de/",
        },
    )

    if role in (*PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert_message_in_log(
            "ERROR    Only one contact per location can have an empty area of responsibility.",
            caplog,
        )
        assert (
            "Only one contact per location can have an empty area of responsibility."
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
def test_phone_number_conversion() -> None:
    """
    Test that phone numbers are converted to the expected international format.
    """
    variants = [
        "+49123456789",
        "0123456789",
        "012 34/56789",
        "01234-56789",
        "0049123456789",
        "00 (49) (1234) 56789",
        " +49/1234-56789",
    ]
    for variant in variants:
        form_data = {
            "location": POI_ID,
            "area_of_responsibility": "test",
            "name": "",
            "email": "mail@mail.integreat",
            "phone_number": variant,
            "website": "https://integreat-app.de/",
        }

        form = ContactForm(
            data=form_data,
            instance=None,
            additional_instance_attributes={"region": REGION_SLUG},
        )
        form.is_valid()  # this is not an assert, because it would fail. calling is_valid() is required to populate cleaned_data.
        cleaned = form.clean()
        assert cleaned["phone_number"] == "+49 (0) 123456789"
