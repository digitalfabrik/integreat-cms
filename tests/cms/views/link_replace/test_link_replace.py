from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.contrib.contenttypes.models import ContentType

from integreat_cms.cms.models import PageTranslation, Region
from integreat_cms.cms.utils.linkcheck_utils import find_target_url_per_content

REGION: str = "nurnberg"

# list of tuple (<link types to replace>, <URLs that should be replaced>, <type and id of content that have URLs listed before>)
parameters = [
    (
        ["invalid"],
        ["https://tuerantuer.dx/", "https://integreat.app/fake-region/de/willkommen/"],
        (PageTranslation, 99),
    ),
    (
        ["internal"],
        [
            "https://integreat.app/fake-region/de/willkommen/",
            "https://integreat.app/augsburg/de/willkommen/",
        ],
        (PageTranslation, 99),
    ),
    (
        ["external"],
        ["https://tuerantuer.dx/", "https://tuerantuer.de/"],
        (PageTranslation, 99),
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", parameters)
def test_find_target_url_per_content_invalid_links(
    load_test_data: None,
    parameter: tuple[list[str], list[str], tuple[ContentType, int]],
) -> None:
    """
    Test link filter per selected link type(s) is working correctly.
    """
    link_types, target_urls, target_content_detail = parameter

    # "d" is something many of our links can contain thanks to ".de" or language slug "de"
    result = find_target_url_per_content(
        "d", "d", Region.objects.filter(slug=REGION).first(), link_types
    )

    content_type, content_id = target_content_detail
    target_content = content_type.objects.filter(id=content_id).first()
    for content, urls in result.items():
        assert content == target_content
        assert len(urls) == len(target_urls)
        for url in urls:
            assert url in target_urls
