import json
import re

import pytest
from django.test.client import Client
from django.urls import reverse
from lxml.html import fromstring, tostring
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.utils.content_utils import update_contacts
from tests.conftest import AUTHOR, EDITOR, MANAGEMENT, STAFF_ROLES

REGION_SLUG = "augsburg"
CONTACT1 = {
    "id": 3,
    "json": {
        "url": "/augsburg/contact/3/",
        "name": "Integrationsberatung: Mariana Musterfrau (mariana-musterfrau@example.com, +49 (0) 123456789, https://integreat-app.de/)| Linked location: Draft location Viktoriastraße 1 86150 Augsburg",
        "details": {
            "address": "show address",
            "area_of_responsibility": "show area of responsibility",
            "name": "show name",
            "email": "show email",
            "phone_number": "show phone number",
            "website": "show website",
        },
    },
    "details": "name,email",
    "card": '<div><div contenteditable="false" data-contact-id="3" data-contact-url="/augsburg/contact/3/?details=name,email" class="contact-card notranslate" dir="ltr" translate="no"><a href="/augsburg/contact/3/?details=name,email" style="display: none">Contact</a><h4>Mariana Musterfrau</h4><p><img src="http://localhost:8000/static/svg/email.svg" alt="Email: " width="15" height="15"/><a href="mailto:mariana-musterfrau@example.com">mariana-musterfrau@example.com</a></p></div></div>',
    "stub": '<div><div data-contact-id="3" data-contact-url="/augsburg/contact/3/?details=name,email"></div></div>',
}

CONTACT2 = {
    "json": {
        "url": "/augsburg/contact/4/",
        "name": "(generalcontactinformation@example.com, +49 (0) 123456789, https://integreat-app.de/)| Linked location: Draft location Viktoriastraße 1 86150 Augsburg",
        "details": {
            "address": "show address",
            "email": "show email",
            "phone_number": "show phone number",
            "website": "show website",
        },
    },
    "card": '<div><div contenteditable="false" data-contact-id="4" data-contact-url="/augsburg/contact/4/?details=phone_number" class="contact-card notranslate" dir="ltr" translate="no"><a href="/augsburg/contact/4/?details=phone_number" style="display: none">Contact</a><p><img src="http://localhost:8000/static/svg/call.svg" alt="Phone Number: " width="15" height="15"><a href="tel:+49123456789">+49 (0) 123456789</a></p></div></div>',
    "stub": '<div><div data-contact-id="4" data-contact-url="/augsburg/contact/4/?details=phone_number"></div></div>',
}


def strip(arg: str | object) -> str:
    return re.sub(r"\s+", "", str(arg), flags=re.UNICODE)


@pytest.mark.django_db
def test_search_contact_single(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that querying for a specific contact returns that contact to authorized users
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    response = client.post(
        reverse(
            "search_contact_ajax",
            kwargs={
                "region_slug": REGION_SLUG,
            },
        ),
        json.dumps(
            {
                "query_string": "Mariana Musterfrau",
            }
        ),
        content_type="application/json",
    )

    if role not in [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR]:
        assert response.status_code in [302, 403]
        return

    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["data"][0] == CONTACT1["json"]


@pytest.mark.django_db
def test_search_contact_multiple(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that querying for a term returns relevant contacts to authorized users
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    response = client.post(
        reverse(
            "search_contact_ajax",
            kwargs={
                "region_slug": REGION_SLUG,
            },
        ),
        json.dumps(
            {
                "query_string": "show address",
            }
        ),
        content_type="application/json",
    )

    if role not in [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR]:
        assert response.status_code in [302, 403]
        return

    assert response.status_code == 200
    response = json.loads(response.content.decode("utf-8"))["data"]
    assert CONTACT1["json"] in response
    assert CONTACT2["json"] in response


@pytest.mark.django_db
def test_get_contact_card(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that requesting a contact card returns it to authorized users with only the selected details
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    response = client.get(
        reverse(
            "get_contact",
            kwargs={
                "region_slug": REGION_SLUG,
                "contact_id": CONTACT1["id"],
            },
        ),
        {"details": CONTACT1["details"]},
    )

    if role not in [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR]:
        assert response.status_code in [302, 403]
        return

    assert response.status_code == 200
    assert strip(response.content.decode("utf-8")) == strip(CONTACT1["card"])


@pytest.mark.django_db
def test_get_contact_card_raw(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that requesting a raw contact representation returns it to authorized users
    """
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user

    response = client.get(
        reverse(
            "get_contact_raw",
            kwargs={
                "region_slug": REGION_SLUG,
                "contact_id": CONTACT1["id"],
            },
        ),
    )

    if role not in [*STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR]:
        assert response.status_code in [302, 403]
        return

    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["data"] == CONTACT1["json"]


@pytest.mark.django_db
def test_update_contact_card_single(
    load_test_data: None,
) -> None:
    """
    Test that a contact card is correctly recognized,
    and the card stub replaced by the contact card with selected details
    """
    stub = fromstring(CONTACT1["stub"])
    card = fromstring(CONTACT1["card"])

    update_contacts(stub)
    assert strip(tostring(stub, encoding="unicode", with_tail=False)) == strip(
        tostring(card, encoding="unicode", with_tail=False)
    )


@pytest.mark.django_db
def test_update_contact_card_multiple(
    load_test_data: None,
) -> None:
    """
    Test that multiple contact cards are correctly recognized,
    and the card stubs replaced by the contact cards with selected details
    """
    content = fromstring(f"{CONTACT1['stub']}{CONTACT2['stub']}")
    card1 = strip(
        tostring(fromstring(CONTACT1["card"]), encoding="unicode", with_tail=False)
    )
    card2 = strip(
        tostring(fromstring(CONTACT2["card"]), encoding="unicode", with_tail=False)
    )

    update_contacts(content)
    result = strip(tostring(content, encoding="unicode", with_tail=False))
    assert card1 in result
    assert card2 in result
