import io

from urllib.parse import urlencode, quote

import pytest
import pypdf

from django.urls import reverse


# pylint: disable=unused-argument,too-many-locals
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
            [1, 2, 3, 4, 5, 6, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 26],
            "",
            "92ff67bd01/Integreat - Deutsch - Augsburg.pdf",
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
    load_test_data,
    client,
    admin_client,
    language_slug,
    page_ids,
    url,
    expected_filename,
):
    """
    Test whether the PDF export works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param client: The fixture providing the anonymous user
    :type client: :fixture:`client`

    :param admin_client: The fixture providing the logged in admin
    :type admin_client: :fixture:`admin_client`

    :param language_slug: The language slug of this export
    :type language_slug: str

    :param page_ids: The pages that should be exported
    :type page_ids: list

    :param url: The url query param for the API request
    :type url: str

    :param expected_filename: What filename to expect
    :type expected_filename: str
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
        result_pdf = pypdf.PdfReader(io.BytesIO(b"".join(response.streaming_content)))
        # pylint: disable=consider-using-with
        expected_pdf = pypdf.PdfReader(
            open(f"tests/pdf/files/{expected_filename}", "rb")
        )
        # Assert that both documents have same number of pages
        assert len(result_pdf.pages) == len(expected_pdf.pages)
        # Assert that the content is identical
        for page_number, result_page in enumerate(result_pdf.pages):
            expected_page = expected_pdf.pages[page_number]
            assert result_page.artbox == expected_page.artbox
            assert result_page.bleedbox == expected_page.bleedbox
            assert result_page.cropbox == expected_page.cropbox
            assert result_page.mediabox == expected_page.mediabox
            assert result_page.extract_text() == expected_page.extract_text()
            assert result_page.get_contents() == expected_page.get_contents()


# pylint: disable=unused-argument,too-many-locals
@pytest.mark.django_db
# Override urls to serve PDF files
@pytest.mark.urls("tests.pdf.dummy_django_app.static_urls")
def test_pdf_export_invalid(load_test_data, client, admin_client):
    """
    Test whether the PDF export throws the correct errors

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param client: The fixture providing the anonymous user
    :type client: :fixture:`client`

    :param admin_client: The fixture providing the logged in admin
    :type admin_client: :fixture:`admin_client`
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
