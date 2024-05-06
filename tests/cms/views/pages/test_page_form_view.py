from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client

import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Language, Page, PageTranslation, Region


@pytest.mark.django_db
def test_save_page_translation(
    load_test_data: None,
    login_root_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:
    # Log the user in
    client = login_root_user

    # Get a region that already exists and has active languages
    region = Region.objects.get(slug="testumgebung")
    german_language = Language.objects.get(slug="de")
    page = Page.objects.create(region=region, lft=1, rgt=2, tree_id=1, depth=1)

    PageTranslation.objects.create(
        page=page,
        slug="testcase",
        language=german_language,
        content="<p>testcase</p>",
    )

    url = reverse(
        "edit_page",
        kwargs={
            "region_slug": region.slug,
            "language_slug": german_language.slug,
            "page_id": page.id,
        },
    )

    response = client.post(
        url,
        data={
            "content": "test",
            "mirrored_page_region": "",
            "title": "My test page",
            "slug": "my-test-page",
            "status": "PUBLIC",
            "_position": "first-child",
        },
    )

    assert response.status_code == 302

    response = client.post(
        url,
        data={
            "content": "test123",
            "mirrored_page_region": "",
            "title": "My test page",
            "slug": "my-test-page",
            "status": "PUBLIC",
            "_position": "first-child",
        },
    )

    assert response.status_code == 302

    mutated_translation = PageTranslation.objects.get(slug="testcase")

    print(PageTranslation.objects.filter(content="test123").count())

    assert mutated_translation.content == "test123"
