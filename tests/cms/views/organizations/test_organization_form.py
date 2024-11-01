from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import MediaFile, Organization, Page, POI, Region
from tests.conftest import ANONYMOUS, MANAGEMENT, STAFF_ROLES


@pytest.mark.django_db
def test_poi_form_shows_no_contents(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
) -> None:
    """
    Test that no contents are shown in the organization form if it does not have any content assinged
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    new_organization = Organization.objects.create(
        name="New Organization",
        slug="new-organization",
        icon=MediaFile.objects.filter(id=1).first(),
        region=Region.objects.filter(id=1).first(),
        website="https://integreat-app.de/",
    )

    edit_organization = reverse(
        "edit_organization",
        kwargs={
            "organization_id": new_organization.id,
            "region_slug": new_organization.region.slug,
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
    # Choose an organization which has a page and a poi assigned
    ORGANIZATION_ID = 1

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

    organization = Organization.objects.filter(id=ORGANIZATION_ID).first()
    organization_pages = list(organization.pages.all())
    organization_pois = list(organization.pois.all())

    region = organization.region

    assert len(organization_pages) > 0
    assert len(organization_pois) > 0

    edit_organization = reverse(
        "edit_organization",
        kwargs={
            "organization_id": organization.id,
            "region_slug": region.slug,
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
