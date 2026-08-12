from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.test.client import Client
    from pytest_django.fixtures import Settings

    from integreat_cms.cms.models import Page

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from integreat_cms.cms.models import Language, PageTranslation, Region


@pytest.mark.django_db
def test_case_insensitive_unique_slug(
    client: Client,
    load_test_data: None,
    settings: Settings,
    create_page: Callable[..., Page],
) -> None:
    """
    Test that an appropriate message is shown to users and the view does not crash when slug is updated for uniqueness
    """
    settings.LANGUAGE_CODE = "en"

    region = Region.objects.get(slug="augsburg")
    language = Language.objects.get(slug="de")

    page = create_page(region=region)
    PageTranslation.objects.create(page=page, language=language, slug="slug")

    assert PageTranslation.objects.filter(slug="slug").count() == 1
    assert PageTranslation.objects.filter(slug="slug-2").count() == 0

    user = get_user_model().objects.get(username="service_team")
    client.force_login(user)

    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": region.slug,
            "language_slug": language.slug,
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "",
            "title": "Slug",
            "slug": "Slug",
            "icon": "",
            "treebeard_ref_node": 2,
            "treebeard_position": "right",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302

    redirect_url = response.headers.get("location")

    assert (
        "The slug was changed from &#x27;Slug&#x27; to &#x27;slug-2&#x27;."
        in client.get(redirect_url).content.decode("utf-8")
    )

    assert PageTranslation.objects.filter(slug="slug").count() == 1
    assert PageTranslation.objects.filter(slug="slug-2").count() == 1
