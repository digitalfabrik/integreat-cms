from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import MediaFile, Organization, Page, POI, Region
from tests.conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES, MANAGEMENT, STAFF_ROLES
from tests.utils import assert_message_in_log

# Choose a region
REGION_SLUG = "augsburg"
# An organization which has a page and a poi assigned and belongs to the above chosen region
REFERENCED_ORGANIZATION_ID = 1
# An organization which does not have a page and a poi assigned and belongs to the above chosen region
NOT_REFERENCED_ORGANIZATION_ID = 3
# Choose a name which is not used by any organization
NEW_ORGANIZATION_NAME = "New Organization"


@pytest.mark.django_db
def test_organization_form_shows_no_contents(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that no contents are shown in the organization form if it does not have any content assigned
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    edit_organization = reverse(
        "edit_organization",
        kwargs={
            "organization_id": NOT_REFERENCED_ORGANIZATION_ID,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.get(edit_organization)

    if role in STAFF_ROLES + [MANAGEMENT]:
        assert (
            "This organization currently has no maintained pages."
            in response.content.decode("utf-8")
        )
        assert (
            "This organization currently has no maintained locations."
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_organization}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_organization_form_shows_associated_contents(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Nicht archivierte Organisation in Augsburg has two pages and one location.
    They must be shown in the form.
    """

    # To check contents that do not belong to the organization do not appear in the form,
    # choose a page and a POI
    #   - 1) that do not belong to the organization chosen above
    # and
    #   - 2) whose titles are not contained in the titles of pages and organizations that belong to the organization
    # (Currently page "Willkommen in Augsburg" is assigned to the organization with id=1.
    #  If page "Willkommen" is used for this check, the test fails even though the system is working as expected.)

    NON_ORGANIZATION_PAGE_ID = 5
    NON_ORGANIZATION_POI_ID = 6

    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    organization = Organization.objects.filter(id=REFERENCED_ORGANIZATION_ID).first()
    organization_pages = list(organization.pages.all())
    organization_pois = list(organization.pois.all())

    region = organization.region

    assert len(organization_pages) > 0
    assert len(organization_pois) > 0

    edit_organization = reverse(
        "edit_organization",
        kwargs={
            "organization_id": REFERENCED_ORGANIZATION_ID,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.get(edit_organization)

    non_organization_page = Page.objects.filter(id=NON_ORGANIZATION_PAGE_ID).first()
    non_organization_poi = POI.objects.filter(id=NON_ORGANIZATION_POI_ID).first()

    if role in STAFF_ROLES + [MANAGEMENT]:
        for content in organization_pages + organization_pois:
            assert content.get_translation(
                region.default_language.slug
            ).title in response.content.decode("utf-8")
            if not region.default_language.slug == "en":
                if english_translation := content.get_translation("en"):
                    english_translation.title in response.content.decode("utf-8")
                else:
                    "Translation not available" in response.content.decode("utf-8")
        assert non_organization_page.get_translation(
            region.default_language.slug
        ).title not in response.content.decode("utf-8")
        assert non_organization_poi.get_translation(
            region.default_language.slug
        ).title not in response.content.decode("utf-8")

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_organization}"
        )

    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_create_new_organization(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test an organization will be created as expected
    """
    client, role = login_role_user

    settings.LANGUAGE_CODE = "en"

    assert not Organization.objects.filter(name=NEW_ORGANIZATION_NAME).exists()

    new_organization = reverse(
        "new_organization",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_organization,
        data={
            "name": NEW_ORGANIZATION_NAME,
            "slug": "new-organization",
            "icon": 1,
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 302
        assert_message_in_log(
            f'SUCCESS  Organization "{NEW_ORGANIZATION_NAME}" was successfully created',
            caplog,
        )
        edit_url = response.headers.get("location")
        response = client.get(edit_url)
        assert (
            f"Organization &quot;{NEW_ORGANIZATION_NAME}&quot; was successfully created"
            in response.content.decode("utf-8")
        )
        assert Organization.objects.filter(name=NEW_ORGANIZATION_NAME).exists()

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_organization}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_cannot_create_organization_with_duplicate_name(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    No organization should be created with the same name with an existing organization.
    """
    client, role = login_role_user

    settings.LANGUAGE_CODE = "en"

    existing_organization = Organization.objects.filter(
        region__slug=REGION_SLUG
    ).first()
    assert existing_organization

    new_organization = reverse(
        "new_organization",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        new_organization,
        data={
            "name": existing_organization.name,
            "slug": existing_organization.slug,
            "icon": 1,
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 200
        assert_message_in_log(
            "ERROR    Name: An organization with the same name already exists in this region. Please choose another name.",
            caplog,
        )
        assert (
            "An organization with the same name already exists in this region. Please choose another name."
            in response.content.decode("utf-8")
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_organization}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_edit_organization(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test an existing organization is updated as expected
    """
    client, role = login_role_user

    settings.LANGUAGE_CODE = "en"

    edit_organization = reverse(
        "edit_organization",
        kwargs={
            "organization_id": NOT_REFERENCED_ORGANIZATION_ID,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        edit_organization,
        data={
            "name": "I got a new name",
            "slug": "i-got-a-new-name",
            "icon": 1,
            "website": "https://integreat-app.de/",
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 200
        assert_message_in_log(
            'SUCCESS  Organization "I got a new name" was successfully saved',
            caplog,
        )
        assert (
            "Organization &quot;I got a new name&quot; was successfully saved"
            in response.content.decode("utf-8")
        )
        assert (
            Organization.objects.filter(id=NOT_REFERENCED_ORGANIZATION_ID).first().name
            == "I got a new name"
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={edit_organization}"
        )
    else:
        assert response.status_code == 403
