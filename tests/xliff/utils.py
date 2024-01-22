"""
This file contains helper functions for XLIFF tests.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sys
    from typing import Any, Literal, TypedDict

    from typing import NotRequired

    from _pytest.logging import LogCaptureFixture

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import translation_status
from integreat_cms.cms.models import Page

from ..utils import assert_message_in_log

if TYPE_CHECKING:

    class OpenKwargs(TypedDict):
        """
        A custom type for partial keyword arguments to :func:`python:open`
        """

        #: The ``mode`` argument
        mode: Literal["r", "rb"]
        #: The ``encoding`` argument
        encoding: NotRequired[Literal["utf-8"]]


def get_open_kwargs(file_name: str) -> OpenKwargs:
    """
    Determine the ``open()`` keyword arguments of a file (binary mode for ZIP files)

    :param file_name: The filename

    :return: The kwargs
    """
    return (
        {"mode": "rb"}
        if file_name.endswith(".zip")
        else {"mode": "r", "encoding": "utf-8"}
    )


def upload_files(
    client: Client, url: str, file_1: str, file_2: str
) -> HttpResponseNotFound | HttpResponseRedirect:
    """
    Helper function to upload two XLIFF files

    :param client: The authenticated client
    :param url: The URL to which the files should be uploaded
    :param file_1: The first file
    :param file_2: The second file

    :return: The upload response
    """
    import_path = "tests/xliff/files/import"
    with open(f"{import_path}/{file_1}", **get_open_kwargs(file_1)) as f1:
        with open(f"{import_path}/{file_2}", **get_open_kwargs(file_2)) as f2:
            return client.post(url, data={"xliff_file": [f1, f2]}, format="multipart")


def get_and_assert_200(client: Client, url: str) -> HttpResponse | TemplateResponse:
    """
    Perform a get request and make sure the result is successful

    :param client: The authenticated client
    :param url: The URL to open

    :return: The successful response
    """
    # Check if xliff view is correctly rendered
    result = client.get(url)
    print(result.headers)
    assert result.status_code == 200
    return result


def validate_xliff_import_response(
    client: Client,
    caplog: LogCaptureFixture,
    response: HttpResponseRedirect,
    import_1: dict[str, Any],
    import_2: dict[str, Any],
) -> None:
    """
    Helper function to validate an XLIFF import response

    :param client: The authenticated client
    :param caplog: The :fixture:`caplog` fixture
    :param response: The response of the confirm view to be validated
    :param import_1: A dict of import information
    :param import_2: A list of import information
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
            assert_message_in_log(import_n["confirmation_message"], caplog)
    # Check if XLIFF import is correctly confirmed
    caplog.clear()
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
        assert translation.translation_state == translation_status.UP_TO_DATE
        assert_message_in_log(import_n["message"], caplog)
        if translation.version > 1:
            # If a translation already exists for this version, assert that the status is inherited
            previous_translation = page.translations.get(
                language__slug="en", version=translation.version - 1
            )
            assert previous_translation.status == translation.status
        else:
            # Else, the status should be inherited from the source translation
            assert translation.source_translation.status == translation.status
