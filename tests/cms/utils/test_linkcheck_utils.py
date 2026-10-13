from __future__ import annotations

import pytest
from django.contrib.contenttypes.models import ContentType
from linkcheck.models import Link, Url

from integreat_cms.cms.models import PageTranslation
from integreat_cms.cms.utils.linkcheck_utils import filter_urls

#: The page translation of the test data which contains a contact card
PAGE_TRANSLATION_WITH_CONTACT_CARD_ID: int = 101

#: The url of the contact card of an existing contact (see test data)
EXISTING_CONTACT_URL: str = (
    "/augsburg/contact/5/?details=address,area_of_responsibility,name"
)

#: The url of a contact card whose contact does not exist (anymore)
NON_EXISTING_CONTACT_URL: str = "/augsburg/contact/99999/?details=name"

#: The url of a contact card which is rendered when the contact cannot be found at all
#: (see :func:`~integreat_cms.cms.utils.content_utils.render_contact_card`)
UNKNOWN_REGION_CONTACT_URL: str = "/None/contact/99999/?details=name"


def add_broken_contact_link(url: str) -> Url:
    """
    Add a broken link to a contact card to the page translation which already contains a contact card

    :param url: The url of the contact card
    :return: The newly created url object
    """
    url_object = Url.objects.create(url=url, status=False, error_message="Not found")
    Link.objects.create(
        content_type=ContentType.objects.get_for_model(PageTranslation),
        object_id=PAGE_TRANSLATION_WITH_CONTACT_CARD_ID,
        field="content",
        url=url_object,
        text="Contact",
        ignore=False,
    )
    return url_object


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contact_url",
    [NON_EXISTING_CONTACT_URL, UNKNOWN_REGION_CONTACT_URL],
)
@pytest.mark.parametrize("region_slug", ["augsburg", None])
def test_broken_contact_links_are_excluded(
    load_test_data: None,
    contact_url: str,
    region_slug: str | None,
) -> None:
    """
    Test whether links to contact cards of non-existing contacts are excluded from the link lists,
    just like links to contact cards of existing contacts are.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param contact_url: The url of the broken contact card link
    :param region_slug: The slug of the region to filter by (``None`` means all regions)
    """
    _, count_before = filter_urls(region_slug=region_slug)

    url_object = add_broken_contact_link(contact_url)

    urls, count_after = filter_urls(region_slug=region_slug)
    assert url_object not in urls
    assert count_after == count_before

    invalid_urls, _ = filter_urls(region_slug=region_slug, url_filter="invalid")
    assert url_object not in invalid_urls


@pytest.mark.django_db
@pytest.mark.parametrize("region_slug", ["augsburg", None])
def test_valid_contact_links_are_excluded(
    load_test_data: None,
    region_slug: str | None,
) -> None:
    """
    Test whether links to contact cards of existing contacts are excluded from the link lists

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param region_slug: The slug of the region to filter by (``None`` means all regions)
    """
    urls, _ = filter_urls(region_slug=region_slug)
    assert EXISTING_CONTACT_URL not in [url.url for url in urls]
