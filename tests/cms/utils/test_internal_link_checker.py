from __future__ import annotations

import pytest
from linkcheck.models import Url

from integreat_cms.cms.utils.internal_link_checker import check_internal

VALID_INTERNAL_LINKS: list[str] = [
    "https://integreat.app",
    "https://integreat.app/augsburg",
    "https://integreat.app/augsburg/de",
    "https://integreat.app/augsburg/en",
    "https://integreat.app/augsburg/de/disclaimer",
    "https://integreat.app/augsburg/ar/disclaimer",
    "https://integreat.app/augsburg/de/events",
    "https://integreat.app/augsburg/de/events/test-veranstaltung",
    "https://integreat.app/augsburg/ar/events/test-veranstaltung",
    "https://integreat.app/augsburg/de/locations",
    "https://integreat.app/augsburg/de/locations/test-ort",
    "https://integreat.app/augsburg/ar/locations/test-ort",
    "https://integreat.app/augsburg/de/news/local",
    "https://integreat.app/augsburg/de/news/local/1",
    "https://integreat.app/augsburg/de/news/tu-news",
    "https://integreat.app/augsburg/de/offers/sprungbrett",
    "https://integreat.app/augsburg/de/offers/lehrstellen-radar",
    "https://integreat.app/nurnberg/de/offers/ihk-praktikumsboerse",
    "https://integreat.app/augsburg/de/willkommen/uber-die-app-integreat-augsburg",
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg",
    "https://integreat.app/augsburg/ar/%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D9%88%D8%B5%D9%88%D9%84/%D9%85%D8%B1%D8%AD%D8%A8%D8%A7-%D8%A8%D9%83%D9%85-%D9%81%D9%8A-%D9%85%D8%AF%D9%8A%D9%86%D8%A9-%D8%A3%D9%88%D8%AC%D8%B3%D8%A8%D9%88%D8%B1%D8%AC",
    "https://integreat.app/augsburg/fa/%DA%AF%D8%A7%D9%85-%D9%86%D8%AE%D8%B3%D8%AA/%D9%86%D9%82%D8%B4%D9%87-%D8%B4%D9%87%D8%B1",
    "https://integreat.app/nurnberg/de/events/test-veranstaltung",
    "https://integreat.app/nurnberg/de/locations/test-ort",
]

INVALID_INTERNAL_LINKS: list[str] = [
    "https://integreat.app/non-existing",
    "https://integreat.app/non-existing/de",
    "https://integreat.app/augsburg/non-existing",
    "https://integreat.app/augsburg/de/non-existing",
    "https://integreat.app/augsburg/de/disclaimer/non-existing",
    "https://integreat.app/augsburg/de/events/non-existing/",
    "https://integreat.app/augsburg/de/locations/non-existing",
    "https://integreat.app/augsburg/de/locations/entwurf-ort",
    "https://integreat.app/augsburg/ar/news/local/1",
    "https://integreat.app/nurnberg/de/news",
    "https://integreat.app/nurnberg/ar/news/local/1",
    "https://integreat.app/nurnberg/de/news/local/2",
    "https://integreat.app/nurnberg/de/news/tu-news",
    "https://integreat.app/nurnberg/de/news/tu-news/999",
    "https://integreat.app/augsburg/de/offers/ihk-praktikumsboerse",
    "https://integreat.app/augsburg/de/offers/non-existing",
    "https://integreat.app/nurnberg/de/offers/sprungbrett",
    "https://integreat.app/augsburg/de/non-existing/non-existing",
    "https://integreat.app/augsburg/de/beh%C3%B6rden-und-beratung/beh%C3%B6rden/archiviertes-amt",
    "https://integreat.app/augsburg/de/beh%C3%B6rden-und-beratung/beh%C3%B6rden/archiviertes-amt/nicht-archivierte-details",
    "https://integreat.app/augsburg/hidden/test-hidden-language",
    "https://integreat.app/nurnberg/fa/events/test-veranstaltung",
    "https://integreat.app/nurnberg/ar/locations/test-ort",
]

SKIPPED_INTERNAL_LINKS: list[str] = [
    "https://google.com",
    "#anchor",
    "relative-link",
    "/media/file",
    "mailto:test@integreat-app.de",
    "tel:+123456789",
    "https://integreat.app/augsburg/de/news/tu-news/999",
]


def prepage_url(link: str, trailing_slash: bool) -> Url:
    """
    Make sure a link either has or doesn't have a trailing slash

    :param link: The link
    :param trailing_slash: Whether to ensure the trailing slash
    """
    if trailing_slash and not link.endswith("/"):
        link += "/"
    elif not trailing_slash and link.endswith("/"):
        link = link[:-1]
    url, _ = Url.objects.get_or_create(url=link)
    return url


@pytest.mark.django_db
@pytest.mark.parametrize("link", VALID_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_valid(
    load_test_data: None, link: str, trailing_slash: bool
) -> None:
    """
    Check whether the given internal URL is correctly identified as valid link

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert check_internal(url), f"URL '{link}' is not correctly identified as valid"


@pytest.mark.django_db
@pytest.mark.parametrize("link", INVALID_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_invalid(
    load_test_data: None, link: str, trailing_slash: bool
) -> None:
    """
    Check whether the given internal URL is correctly identified as invalid link

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert not check_internal(
        url
    ), f"URL '{link}' is not correctly identified as invalid"


@pytest.mark.django_db
@pytest.mark.parametrize("link", SKIPPED_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_skipped(
    load_test_data: None, link: str, trailing_slash: bool
) -> None:
    """
    Check whether the given internal URL is correctly skipped

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert check_internal(url) is None, f"URL '{link}' is not skipped"
