import filecmp
import io
import zipfile

from os import listdir
from os.path import isfile, join

import pytest

from lxml.html import fromstring
from django.urls import reverse

from integreat_cms.cms.models import Page

from ..conftest import (
    ANONYMOUS,
    STAFF_ROLES,
    PRIV_STAFF_ROLES,
    MANAGEMENT,
    EDITOR,
    AUTHOR,
    OBSERVER,
)


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
    login_role_user, settings, tmp_path, xliff_version, view, directory
):
    """
    This test checks whether the xliff export works as expected

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user: tuple

    :param settings: The fixture providing the django settings
    :type settings: :fixture:`settings`

    :param tmp_path: The fixture providing the directory for temporary files for this test case
    :type tmp_path: :fixture:`tmp_path`

    :param xliff_version: The XLIFF version to be tested
    :type xliff_version: str

    :param view: The name of the view for the export
    :type view: str

    :param directory: The directory that contains the expected XLIFF files
    :type directory: str
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
            translation = page.get_translation("en")
            if translation:
                assert translation.currently_in_translation
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


# pylint: disable=too-many-locals
@pytest.mark.django_db
def test_xliff_import(login_role_user, settings):
    """
    This test checks whether the xliff import works as expected

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user: tuple

    :param settings: The fixture providing the django settings
    :type settings: :fixture:`settings`
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    client, role = login_role_user
    upload_xliff = reverse(
        "upload_xliff", kwargs={"region_slug": "augsburg", "language_slug": "en"}
    )
    import_path = "tests/xliff/files/import"
    file_1 = "augsburg_de_en_1_2_willkommen.xliff"
    file_2 = "augsburg_de_en_2_1_willkommen-in-augsburg.xliff"
    # Upload once for successful import
    with open(f"{import_path}/{file_1}", encoding="utf-8") as f1:
        with open(f"{import_path}/{file_2}", encoding="utf-8") as f2:
            response1 = client.post(
                upload_xliff, data={"xliff_file": [f1, f2]}, format="multipart"
            )
            print(response1.headers)
    # Upload second time to test unchanged import
    with open(f"{import_path}/{file_1}", encoding="utf-8") as f1:
        with open(f"{import_path}/{file_2}", encoding="utf-8") as f2:
            response2 = client.post(
                upload_xliff, data={"xliff_file": [f1, f2]}, format="multipart"
            )
            print(response2.headers)

    if role in PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR]:
        # Perform test twice to check whether unchanged diffs can be imported as well
        for response, msg in [
            (response1, "successfully"),
            (response2, "without changes"),
        ]:
            # If the role should be allowed to access the view, we expect a successful result
            assert response.status_code == 302
            page_tree = reverse(
                "pages", kwargs={"region_slug": "augsburg", "language_slug": "en"}
            )
            redirect_location = response.headers.get("Location")
            # If errors occur, we get redirected to the page tree
            assert redirect_location != page_tree
            # Check if xliff import view is correctly rendered
            response = client.get(redirect_location)
            print(response.headers)
            assert response.status_code == 200
            assert file_1 in response.content.decode("utf-8")
            assert file_2 in response.content.decode("utf-8")
            # Check if XLIFF import is correctly confirmed
            response = client.post(redirect_location)
            print(response.headers)
            assert response.status_code == 302
            # If the import has been successfully confirmed, we get redirected to the page tree
            assert response.headers.get("Location") == page_tree
            # Check if xliff import view is correctly rendered
            response = client.get(page_tree)
            print(response.headers)
            assert response.status_code == 200
            # Check if existing translations are now updated
            for page in Page.objects.filter(id__in=[1, 2]):
                translation = page.get_translation("en")
                assert translation.title == "Updated title"
                assert translation.content == "<p>Updated content</p>"
                assert not translation.currently_in_translation
                assert (
                    f"Page &quot;{translation.title}&quot; was imported {msg}."
                    in response.content.decode("utf-8")
                )
                if translation.version > 1:
                    # If a translation already exists for this version, assert that the status is inherited
                    previous_translation = page.translations.get(
                        language__slug="en", version=translation.version - 1
                    )
                    assert previous_translation.status == translation.status
                else:
                    # Else, the status should be inherited from the source translation
                    assert translation.source_translation.status == translation.status
    elif role == ANONYMOUS:
        for response in [response1, response2]:
            # For anonymous users, we want to redirect to the login form instead of showing an error
            assert response.status_code == 302
            assert (
                response.headers.get("location")
                == f"{settings.LOGIN_URL}?next={upload_xliff}"
            )
    else:
        for response in [response1, response2]:
            # For logged in users, we want to show an error if they get a permission denied
            assert response.status_code == 403
