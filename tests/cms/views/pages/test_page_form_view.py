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
def test_page_form_view_does_not_mutate_valid_html(
    load_test_data: None,
    login_root_user: Client,
    caplog: LogCaptureFixture,
) -> None:
    client = login_root_user

    region = Region.objects.get(slug="testumgebung")
    german_language = Language.objects.get(slug="de")
    page = Page.objects.create(region=region, lft=1, rgt=2, tree_id=1, depth=1)
    content = "<p>line1\r\nline2<p>"

    def get_latest_test_content() -> str:
        return (
            PageTranslation.objects.filter(slug="my-test-page")
            .latest("version")
            .content
        )

    PageTranslation.objects.create(
        page=page,
        slug="testcase",
        language=german_language,
        content=content,
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
            "content": content,
            "mirrored_page_region": "",
            "title": "My test page",
            "slug": "my-test-page",
            "status": "PUBLIC",
            "_position": "first-child",
        },
    )

    # The most straightforward approach to check if the system has detected changes
    # would be asserting the alert. However, decoding the json_messages cookie and formulating the
    # test assertion can be quite intricate and support for the messages framework in testing
    # scenarios begins from Django version 5.0 onwards.

    assert response.status_code == 302

    assert get_latest_test_content() == content
