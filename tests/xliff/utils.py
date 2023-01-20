"""
This file contains helper functions for XLIFF tests.
"""
from django.urls import reverse

from integreat_cms.cms.models import Page

from ..utils import assert_message_in_response


def get_open_kwargs(file_name):
    """
    Determine the ``open()`` keyword arguments of a file (binary mode for ZIP files)

    :param file_name: The filename
    :type file_name: str

    :return: The kwargs
    :rtype: dict
    """
    return (
        {"mode": "rb"}
        if file_name.endswith(".zip")
        else {"mode": "r", "encoding": "utf-8"}
    )


def upload_files(client, url, file_1, file_2):
    """
    Helper function to upload two XLIFF files

    :param client: The authenticated client
    :type client: django.test.client.Client

    :param url: The URL to which the files should be uploaded
    :type url: str

    :param file_1: The first file
    :type file_1: str

    :param file_2: The second file
    :type file_2: str

    :return: The upload response
    :rtype: django.http.HttpResponse
    """
    import_path = "tests/xliff/files/import"
    # The encoding is determined in get_open_kwargs()
    # pylint: disable=unspecified-encoding
    with open(f"{import_path}/{file_1}", **get_open_kwargs(file_1)) as f1:
        with open(f"{import_path}/{file_2}", **get_open_kwargs(file_2)) as f2:
            return client.post(url, data={"xliff_file": [f1, f2]}, format="multipart")


def get_and_assert_200(client, url):
    """
    Perform a get request and make sure the result is successful

    :param client: The authenticated client
    :type client: django.test.client.Client

    :param url: The URL to open
    :type url: str

    :return: The successful response
    :rtype: django.http.HttpResponse
    """
    # Check if xliff view is correctly rendered
    result = client.get(url)
    print(result.headers)
    assert result.status_code == 200
    return result


def validate_xliff_import_response(client, response, import_1, import_2):
    """
    Helper function to validate an XLIFF import response

    :param client: The authenticated client
    :type client: django.test.client.Client

    :param response: The response of the confirm view to be validated
    :type response: django.http.HttpResponse

    :param import_1: A dict of import information
    :type import_1: dict

    :param import_2: A list of import information
    :type import_2: dict
    """
    # If the role should be allowed to access the view, we expect a successful result
    assert response.status_code == 302
    page_tree = reverse(
        "pages", kwargs={"region_slug": "augsburg", "language_slug": "en"}
    )
    redirect_location = response.headers.get("Location")
    # If errors occur, we get redirected to the page tree
    assert redirect_location != page_tree
    response = get_and_assert_200(client, redirect_location)
    for import_n in [import_1, import_2]:
        expected_file = import_n.get("expected_file") or import_n["file"]
        assert expected_file in response.content.decode("utf-8")
        if "confirmation_message" in import_n:
            assert_message_in_response(import_n["confirmation_message"], response)
    # Check if XLIFF import is correctly confirmed
    response = client.post(redirect_location)
    print(response.headers)
    assert response.status_code == 302
    # If the import has been successfully confirmed, we get redirected to the page tree
    assert response.headers.get("Location") == page_tree
    response = get_and_assert_200(client, page_tree)
    # Check if existing translations are now updated
    for import_n in [import_1, import_2]:
        page = Page.objects.get(id=import_n["id"])
        translation = page.get_translation("en")
        assert translation.title == import_n["title"]
        assert translation.content == import_n["content"]
        assert not translation.currently_in_translation
        assert_message_in_response(import_n["message"], response)
        if translation.version > 1:
            # If a translation already exists for this version, assert that the status is inherited
            previous_translation = page.translations.get(
                language__slug="en", version=translation.version - 1
            )
            assert previous_translation.status == translation.status
        else:
            # Else, the status should be inherited from the source translation
            assert translation.source_translation.status == translation.status
