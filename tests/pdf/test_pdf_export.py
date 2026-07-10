"""
If test-data.json has changed and the PDF Files need changing: Go to the pages list view in the CMS,
- inside the right region and with the right language selected -
and select the ids of the pages needed, based on the parametrization here and then chose the bulk action
to export the published pages as a PDF File.
Save that file under its hash named folder, e.g. if the file is returned under `/pdf/990a572a06/Integreat%20-%20Deutsch%20-%20Augsburg.pdf`,
you save it in the folder "990a572a06" inside /tests/pdf/files/ (and delete the old file)
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

import pypdf
import pytest
from django.urls import reverse

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.test.client import Client


@pytest.mark.django_db
# Override urls to serve PDF files
@pytest.mark.urls("tests.pdf.dummy_django_app.static_urls")
@pytest.mark.parametrize(
    "language_slug,page_ids,url,expected_filename",
    [
        (
            "de",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/de/willkommen/",
            "6262976c99/Integreat - Deutsch - Willkommen.pdf",
        ),
        (
            "de",
            [
                1,
                2,
                3,
                4,
                5,
                6,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                26,
                27,
                28,
                31,
                32,
                33,
            ],
            "",
            "990a572a06/Integreat - Deutsch - Augsburg.pdf",
        ),
        (
            "en",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/en/welcome/",
            "e155c5e38b/Integreat - Englisch - Welcome.pdf",
        ),
        (
            "ar",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/ar/معلومات-الوصول/",
            "3b02f5ea5b/Integreat - Arabisch - معلومات الوصول.pdf",
        ),
        (
            "am",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/am/እንኳን-ደህና-መጡ/",
            "52d22a85dc/Integreat - Amharisch - እንኳን ደህና መጡ.pdf",
        ),
        (
            "uk",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/uk/ласкаво-просимо-в-аугсбург/",
            "28814d44dd/Integreat - Ukrainisch - Ласкаво просимо в Аугсбург.pdf",
        ),
        (
            "el",
            [1, 2, 3, 4, 5, 6],
            "/augsburg/ar/καλώς-ήλθατε-στο-augsburg-2",
            "ba6f45d0ab/Integreat - Griechisch - Καλώς ήλθατε στο Augsburg.pdf",
        ),
    ],
)
def test_pdf_export(
    load_test_data: None,
    client: Client,
    admin_client: Client,
    language_slug: str,
    page_ids: list[int],
    url: str,
    expected_filename: str,
) -> None:
    """
    Test whether the PDF export works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param client: The fixture providing the anonymous user
    :param admin_client: The fixture providing the logged in admin
    :param language_slug: The language slug of this export
    :param page_ids: The pages that should be exported
    :param url: The url query param for the API request
    :param expected_filename: What filename to expect
    """
    kwargs = {"region_slug": "augsburg", "language_slug": language_slug}
    export_pdf = reverse("export_pdf", kwargs=kwargs)
    response_cms = admin_client.post(export_pdf, data={"selected_ids[]": page_ids})
    export_pdf_api = reverse("api:pdf_export", kwargs=kwargs)
    response_api = client.get(f"{export_pdf_api}?{urlencode({'url': url})}")
    # Test both the PDF generation of the CMS as well as the API
    for response in [response_cms, response_api]:
        print(response.headers)
        assert response.status_code == 302
        expected_url = f"/pdf/{quote(expected_filename)}"
        assert response.headers.get("Location") == expected_url
        response = admin_client.get(expected_url)
        print(response.headers)
        assert response.headers.get("Content-Type") == "application/pdf"
        # Compare file content
        result_pdf = pypdf.PdfReader(
            io.BytesIO(b"".join(response.streaming_content)),
        )
        with open(f"tests/pdf/files/{expected_filename}", "rb") as file:
            expected_pdf = pypdf.PdfReader(file)
            # Assert that both documents have same number of pages
            assert len(result_pdf.pages) == len(expected_pdf.pages)
            # Assert that the content is identical
            for page_number in range(len(result_pdf.pages)):
                result_page = result_pdf.pages[page_number]
                expected_page = expected_pdf.pages[page_number]
                assert result_page.artbox == expected_page.artbox
                assert result_page.bleedbox == expected_page.bleedbox
                assert result_page.cropbox == expected_page.cropbox
                assert result_page.mediabox == expected_page.mediabox
                assert result_page.extract_text() == expected_page.extract_text()
                assert result_page.get_contents() == expected_page.get_contents()


@pytest.mark.django_db
# Override urls to serve PDF files
@pytest.mark.urls("tests.pdf.dummy_django_app.static_urls")
def test_pdf_export_invalid(
    load_test_data: None,
    client: Client,
    admin_client: Client,
) -> None:
    """
    Test whether the PDF export throws the correct errors

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param client: The fixture providing the anonymous user
    :param admin_client: The fixture providing the logged in admin
    """
    kwargs = {"region_slug": "augsburg", "language_slug": "de"}
    # Test error when PDF is exported via page tree
    export_pdf_cms = reverse("export_pdf", kwargs=kwargs)
    response_cms = admin_client.post(export_pdf_cms, data={"selected_ids[]": [9999]})
    # Test error when PDF is exported via API
    export_pdf_api = reverse("api:pdf_export", kwargs=kwargs)
    response_api = client.get(f"{export_pdf_api}?url=/augsburg/de/non-existing-page/")
    # Test both the PDF generation of the CMS as well as the API
    for response in [response_cms, response_api]:
        print(response.headers)
        assert response.status_code == 404


@pytest.mark.django_db
# Override urls to serve PDF files
@pytest.mark.urls("tests.pdf.dummy_django_app.static_urls")
def test_pdf_export_api_cache_hit_query_count(
    load_test_data: None,
    client: Client,
    django_assert_num_queries: Callable,
) -> None:
    """
    Assert that the API PDF export endpoint issues a small, constant number
    of SQL queries on a cache hit (i.e. when the PDF file for the requested
    region/language already exists).

    This locks in the performance goal of the rewrite in
    :func:`~integreat_cms.cms.utils.pdf_utils._compute_pdf_hash`: the hashing
    step must not issue one query per page (the old code did
    ``page.get_public_translation()`` and ``page.archived`` per page, plus a
    prefetch of every public translation including ``content``), and must not
    load the ``content`` field of any page into the server process.

    The assertion is on the number of queries because that is the
    regression we care about: someone adding a per-page query (a N+1) or
    re-prefetching full translations will bump the count, and this test will
    catch it. The exact value (5) reflects:

    1. ``Region.objects.get(slug=...)`` in the region middleware
    2. the language tree lookup for the region
    3. the single hash-phase ``PageTranslation ... values_list ... distinct``
       query (the whole point of the rewrite - 1 query for N pages)
    4. the final ``pages.count()`` after exclusion
    5. ``Language.objects.get(slug=...)`` for the filename

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param client: The fixture providing the anonymous user
    :param django_assert_num_queries: The fixture providing the query assertion
    """
    kwargs = {"region_slug": "augsburg", "language_slug": "de"}
    export_pdf_api = reverse("api:pdf_export", kwargs=kwargs)
    # Warmup: ensure the PDF file has been created so the next call is a hit.
    warm = client.get(export_pdf_api)
    assert warm.status_code == 302
    expected_url = warm.headers.get("Location")
    assert expected_url is not None
    # Cache hit: the file exists, so this must not regenerate the PDF.
    # It must also not load the page contents to compute the hash.
    with django_assert_num_queries(5):
        response = client.get(export_pdf_api)
    assert response.status_code == 302
    assert response.headers.get("Location") == expected_url
