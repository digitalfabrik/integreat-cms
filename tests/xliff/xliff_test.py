from __future__ import annotations

import filecmp
import io
import zipfile
from os import listdir
from os.path import isfile, join
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from lxml.html import fromstring

from integreat_cms.cms.constants import translation_status
from integreat_cms.cms.models import Page

from ..conftest import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    MANAGEMENT,
    OBSERVER,
    PRIV_STAFF_ROLES,
    STAFF_ROLES,
)
from .utils import upload_files, validate_xliff_import_response
from .xliff_config import XLIFF_IMPORTS

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper


# pylint: disable=too-many-locals
@pytest.mark.django_db
# Override urls to serve XLIFF files
@pytest.mark.urls("tests.xliff.dummy_django_app.static_urls")
@pytest.mark.parametrize("xliff_version", ["xliff-1.2", "xliff-2.0"])
@pytest.mark.parametrize(
    "view,directory",
    [("download_xliff", "latest"), ("download_xliff_only_public", "only_public")],
)
def test_xliff_export(
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    tmp_path: Path,
    xliff_version: str,
    view: str,
    directory: str,
) -> None:
    """
    This test checks whether the xliff export works as expected

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param tmp_path: The fixture providing the directory for temporary files for this test case
    :param xliff_version: The XLIFF version to be tested
    :param view: The name of the view for the export
    :param directory: The directory that contains the expected XLIFF files
    """
    # Override used XLIFF version
    settings.XLIFF_EXPORT_VERSION = xliff_version
    client, role = login_role_user
    export_xliff = reverse(
        view, kwargs={"region_slug": "augsburg", "language_slug": "en"}
    )
    response = client.post(
        export_xliff, data={"selected_ids[]": [1, 2, 3, 4, 5, 14, 15]}
    )
    print(response.headers)
    if role in STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        page_tree = reverse(
            "pages", kwargs={"region_slug": "augsburg", "language_slug": "en"}
        )
        assert response.headers.get("Location") == page_tree
        response = client.get(page_tree)
        print(response.headers)
        # The download link to the xliff file is contained in the message
        parsed_content = fromstring(response.content.decode("utf-8"))
        download_links = [
            link.attrib["href"]
            for link in parsed_content.iter("a")
            if "data-auto-download" in link.attrib
        ]
        print(download_links)
        assert len(download_links) == 1
        response = client.get(download_links[0])
        print(response.headers)
        print(response.status_code)
        assert response.status_code == 200
        # Check if zip can be unzipped and contains the correct xliff files
        file = io.BytesIO(response.getvalue())
        expected_result_dir = f"tests/xliff/files/export/{xliff_version}/{directory}"
        with zipfile.ZipFile(file, "r") as zipped_file:
            assert zipped_file.testzip() is None
            assert set(zipped_file.namelist()) == {
                filename
                for filename in listdir(expected_result_dir)
                if isfile(join(expected_result_dir, filename))
            }
            zipped_file.extractall(path=tmp_path)
            for xliff_file in zipped_file.namelist():
                assert filecmp.cmp(
                    f"{tmp_path}/{xliff_file}", f"{expected_result_dir}/{xliff_file}"
                )
        # Check if existing translations are now "currently in translation"
        for page in Page.objects.filter(id__in=[1, 2]):
            if translation := page.get_translation("en"):
                assert translation.currently_in_translation
                assert (
                    translation.translation_state == translation_status.IN_TRANSLATION
                )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={export_xliff}"
        )
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "import_1,import_2",
    XLIFF_IMPORTS,
)
def test_xliff_import(
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    import_1: dict[str, Any],
    import_2: dict[str, Any],
) -> None:
    """
    This test checks whether the xliff import works as expected

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param settings: The fixture providing the django settings
    :param import_1: A dict of import information
    :param import_2: A list of import information
    :param caplog: The :fixture:`caplog` fixture
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user
    upload_xliff = reverse(
        "upload_xliff", kwargs={"region_slug": "augsburg", "language_slug": "en"}
    )
    response = upload_files(client, upload_xliff, import_1["file"], import_2["file"])
    # Check which role uploaded the files
    if role in PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR]:
        validate_xliff_import_response(
            client,
            caplog,
            response,
            import_1,
            import_2,
        )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={upload_xliff}"
        )
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403
