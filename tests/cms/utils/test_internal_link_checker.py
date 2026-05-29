from __future__ import annotations

import unicodedata

import pytest
from linkcheck.models import Url

from integreat_cms.cms.utils.internal_link_checker import (
    check_internal,
    normalise_internal_path,
)

# A known-valid Arabic page URL (see VALID_INTERNAL_LINKS) used to build
# equivalent-but-byte-different variants for the Unicode-normalisation tests.
_ARABIC_VALID_LINK = (
    "https://integreat.app/augsburg/ar/"
    "%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D9%88%D8%B5%D9%88%D9%84/"
    "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7-%D8%A8%D9%83%D9%85-%D9%81%D9%8A-"
    "%D9%85%D8%AF%D9%8A%D9%86%D8%A9-%D8%A3%D9%88%D8%AC%D8%B3%D8%A8%D9%88%D8%B1%D8%AC"
)

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
    "https://integreat.app/augsburg/fa/locations/test-ort",
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
    load_test_data: None,
    link: str,
    trailing_slash: bool,
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
    load_test_data: None,
    link: str,
    trailing_slash: bool,
) -> None:
    """
    Check whether the given internal URL is correctly identified as invalid link

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert not check_internal(
        url,
    ), f"URL '{link}' is not correctly identified as invalid"


@pytest.mark.django_db
@pytest.mark.parametrize("link", SKIPPED_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_skipped(
    load_test_data: None,
    link: str,
    trailing_slash: bool,
) -> None:
    """
    Check whether the given internal URL is correctly skipped

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert check_internal(url) is None, f"URL '{link}' is not skipped"


# Variants of a known-valid link (see VALID_INTERNAL_LINKS) that previously
# tripped the URL-equality comparison in ``check_translation_link`` because
# query strings, fragments and percent-encoded slugs were not normalised on
# both sides. These should all be treated as the same target and resolve to
# the same translation.
NORMALISED_VALID_LINKS: list[str] = [
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg?utm_source=email",
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg/?utm_source=email",
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg#section-1",
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg/?utm_source=email&ref=foo#section-1",
    # Percent-encoded Unicode slug carrying a query string.
    "https://integreat.app/augsburg/ar/%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D9%88%D8%B5%D9%88%D9%84/%D9%85%D8%B1%D8%AD%D8%A8%D8%A7-%D8%A8%D9%83%D9%85-%D9%81%D9%8A-%D9%85%D8%AF%D9%8A%D9%86%D8%A9-%D8%A3%D9%88%D8%AC%D8%B3%D8%A8%D9%88%D8%B1%D8%AC?utm=x",
    # Lowercase percent-encoding of the same slug — unquote is case-insensitive.
    "https://integreat.app/augsburg/ar/%d9%85%d8%b9%d9%84%d9%88%d9%85%d8%a7%d8%aa-%d8%a7%d9%84%d9%88%d8%b5%d9%88%d9%84/%d9%85%d8%b1%d8%ad%d8%a8%d8%a7-%d8%a8%d9%83%d9%85-%d9%81%d9%8a-%d9%85%d8%af%d9%8a%d9%86%d8%a9-%d8%a3%d9%88%d8%ac%d8%b3%d8%a8%d9%88%d8%b1%d8%ac",
]


@pytest.mark.django_db
@pytest.mark.parametrize("link", NORMALISED_VALID_LINKS)
def test_check_internal_normalised_equivalents(
    load_test_data: None,
    link: str,
) -> None:
    """
    URLs that differ from a known-valid link only by query string, fragment,
    or percent-encoding must still be classified as valid.
    """
    url, _ = Url.objects.get_or_create(url=link)
    assert check_internal(url), f"URL '{link}' is not correctly identified as valid"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/augsburg/de/welcome/", "augsburg/de/welcome"),
        ("augsburg/de/welcome", "augsburg/de/welcome"),
        ("/augsburg/de/welcome/?utm_source=email", "augsburg/de/welcome"),
        ("/augsburg/de/welcome/#section", "augsburg/de/welcome"),
        ("/augsburg/de/welcome/?x=1#y", "augsburg/de/welcome"),
        ("https://integreat.app/augsburg/de/welcome/", "augsburg/de/welcome"),
        ("/augsburg/ar/%D9%85%D8%B1%D8%AD%D8%A8%D8%A7/", "augsburg/ar/مرحبا"),
        ("/augsburg/ar/%d9%85%d8%b1%d8%ad%d8%a8%d8%a7/", "augsburg/ar/مرحبا"),
        # 1. Unicode normalisation: NFD decomposes ``إ`` (U+0625) into
        #    ``ا`` + combining hamza below (U+0627 + U+0655). Both forms
        #    render identically and must compare equal.
        ("/augsburg/ar/إ/", "augsburg/ar/إ"),
        ("/augsburg/ar/إ/", "augsburg/ar/إ"),
        # 2. Cased non-Latin scripts (and ASCII): slugify lower-cases.
        ("/Augsburg/DE/Welcome/", "augsburg/de/welcome"),
        # Cyrillic uppercase ``К`` (U+041A) should fold to ``к`` (U+043A).
        ("/region/ru/Киев/", "region/ru/киев"),
        # 3. Format-category characters (Cf) are stripped: LRM, RLM, ZWJ,
        #    ZWNJ, and the various Unicode embedding/isolate marks.
        ("/augsburg/ar/‎marhaba/", "augsburg/ar/marhaba"),
        ("/augsburg/ar/‏marhaba/", "augsburg/ar/marhaba"),
        ("/augsburg/ar/mar‍haba/", "augsburg/ar/marhaba"),
        ("/augsburg/ar/mar‌haba/", "augsburg/ar/marhaba"),
        ("/augsburg/ar/⁦marhaba⁩/", "augsburg/ar/marhaba"),
    ],
)
def test_normalise_internal_path(path: str, expected: str) -> None:
    """
    Direct unit test for the path-normalisation helper: query strings,
    fragments, percent-encoding casing, Unicode normalisation form,
    letter case in cased scripts, and invisible format-category
    characters are all collapsed to a single canonical form.
    """
    assert normalise_internal_path(path) == expected


def test_normalise_internal_path_nfd_equals_nfc() -> None:
    """
    Property-style check: any string and its NFD decomposition must
    normalise to the same value. Pins the contract that the helper
    matches ``slugify``'s NFKC step regardless of input form.
    """
    nfc = "/augsburg/ar/مرحبا-بكم-في-مدينة-أوجسبورج/"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfd != nfc  # sanity: the decomposed form really differs byte-wise
    assert normalise_internal_path(nfd) == normalise_internal_path(nfc)


# Integration regressions: each variant of a known-valid link below differs
# from the canonical form only in a way the helper now normalises. They
# should all be accepted by the full ``check_internal`` pipeline.
NFD_ARABIC_LINK = unicodedata.normalize("NFD", _ARABIC_VALID_LINK)
LRM_INJECTED_ARABIC_LINK = (
    _ARABIC_VALID_LINK[: len("https://integreat.app/augsburg/ar/")]
    + "‎"
    + _ARABIC_VALID_LINK[len("https://integreat.app/augsburg/ar/") :]
)
UPPERCASE_ENGLISH_LINK = (
    "https://integreat.app/augsburg/en/welcome/About-The-Integreat-App-Augsburg"
)


UNICODE_NORMALISED_VALID_LINKS: list[str] = [
    NFD_ARABIC_LINK,
    LRM_INJECTED_ARABIC_LINK,
    UPPERCASE_ENGLISH_LINK,
]


@pytest.mark.django_db
@pytest.mark.parametrize("link", UNICODE_NORMALISED_VALID_LINKS)
def test_check_internal_unicode_normalisation(
    load_test_data: None,
    link: str,
) -> None:
    """
    Links that differ from a known-valid target only by Unicode
    normalisation form, by an injected bidi-control character, or by
    letter case must still resolve and be classified as valid.
    """
    url, _ = Url.objects.get_or_create(url=link)
    assert check_internal(url), f"URL '{link}' is not correctly identified as valid"
