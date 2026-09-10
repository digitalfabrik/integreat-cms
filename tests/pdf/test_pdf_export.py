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
            assert len(result_pdf.pages) == len(expected_pdf.pages)
            for page_number in range(len(result_pdf.pages)):
                result_page = result_pdf.pages[page_number]
                expected_page = expected_pdf.pages[page_number]
                assert result_page.mediabox == expected_page.mediabox
                assert result_page.extract_text() == expected_page.extract_text()


def _outline_titles(outline: list, level: int = 0) -> list[tuple[str, int]]:
    """
    Flatten the outline of a PDF document into its titles and nesting levels

    :param outline: The outline of the PDF document or one of its sub-lists
    :param level: The nesting level of the given outline
    :return: The title and nesting level of each entry of the outline
    """
    titles = []
    for entry in outline:
        if isinstance(entry, list):
            titles += _outline_titles(entry, level + 1)
        else:
            titles.append((entry.title, level))
    return titles


@pytest.mark.django_db
# Override urls to serve PDF files
@pytest.mark.urls("tests.pdf.dummy_django_app.static_urls")
def test_pdf_export_structure(
    load_test_data: None,
    admin_client: Client,
) -> None:
    """
    Test whether the PDF export contains the page tree as outline and a footer on each page

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param admin_client: The fixture providing the logged in admin
    """
    kwargs = {"region_slug": "augsburg", "language_slug": "de"}
    export_pdf = reverse("export_pdf", kwargs=kwargs)
    response = admin_client.post(
        export_pdf, data={"selected_ids[]": [1, 2, 3, 4, 5, 6]}
    )
    assert response.status_code == 302
    response = admin_client.get(response.headers["Location"])
    result_pdf = pypdf.PdfReader(io.BytesIO(b"".join(response.streaming_content)))
    # The hierarchy of the pages should be reflected in the outline of the PDF
    assert _outline_titles(result_pdf.outline) == [
        ("Willkommen", 0),
        ("Wissenswertes über Augsburg", 1),
        ("Über die App Integreat Augsburg", 1),
        ("Willkommen in Augsburg", 1),
        ("Stadtplan", 1),
        ("Kontakt zu App Team Augsburg", 1),
    ]
    # The footer should be repeated on every page
    for page in result_pdf.pages:
        assert "Stadt Augsburg" in page.extract_text()


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
