from __future__ import annotations

import os
from urllib import parse

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Directory, MediaFile
from tests.conftest import (
    ANONYMOUS,
    HIGH_PRIV_STAFF_ROLES,
    PRIV_STAFF_ROLES,
    STAFF_ROLES,
)


@pytest.mark.django_db
def test_directory_path(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    query = parse.urlencode(
        {
            "directory": 1,
        }
    )
    next_url = reverse("mediacenter_directory_path")
    url = f"{next_url}?{query}"

    response = client.get(url)

    if role in STAFF_ROLES:
        assert response.status_code == 200
        # Check contents in the response
        assert "Test Directory" in response.content.decode("utf-8")
        assert not "Empty Directory" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_get_directory_content(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    query = parse.urlencode(
        {
            "directory": 1,
        }
    )
    next_url = reverse("mediacenter_get_directory_content")
    url = f"{next_url}?{query}"

    response = client.get(url)

    if role in STAFF_ROLES:
        assert response.status_code == 200
        # Check contents in the response
        assert "Test Logo" in response.content.decode("utf-8")
        assert not "Test Logo 2" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_create_directory(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user
    next_url = url = reverse("mediacenter_create_directory")

    # A new directory without parent directoy
    response_directory = client.post(url, data={"name": "new directory"})
    # A new sub directory
    response_sub_directory = client.post(
        url, data={"name": "sub directory", "parent": 1}
    )

    if role in PRIV_STAFF_ROLES:
        assert response_directory.status_code == 200
        assert response_sub_directory.status_code == 200
        # Verify that the directories were actually created
        assert Directory.objects.filter(name="new directory").count() == 1
        assert Directory.objects.filter(parent__id=1).first().name == "sub directory"
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_directory.status_code == 302
        assert response_sub_directory.status_code == 302
        assert (
            response_directory.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
        assert (
            response_sub_directory.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response_directory.status_code == 403
        assert response_sub_directory.status_code == 403


@pytest.mark.django_db
def test_edit_directory(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_edit_directory")

    # Test with unchanged input
    response_without_change = client.post(
        url,
        data={
            "id": 1,
            "name": "Test Directory",
            "is_hidden": False,
        },
    )
    # Test with changed input
    response_with_change = client.post(
        url,
        data={
            "id": 1,
            "name": "New Directory Name",
            "is_hidden": False,
        },
    )

    if role in PRIV_STAFF_ROLES:
        assert response_without_change.status_code == 200
        assert response_with_change.status_code == 200
        # Check the directoy was renamed
        assert Directory.objects.filter(id=1).first().name == "New Directory Name"
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_without_change.status_code == 302
        assert response_with_change.status_code == 302
        assert (
            response_without_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
        assert (
            response_with_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response_without_change.status_code == 403
        assert response_with_change.status_code == 403


@pytest.mark.django_db
def test_delete_directory(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_delete_directory")

    response_success = client.post(url, data={"id": 2})
    response_fail = client.post(url, data={"id": 1})

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response_success.status_code == 200
        assert response_fail.status_code == 400
        # Check that the directory was deleted/still exists
        assert not Directory.objects.filter(id=2).count()
        assert Directory.objects.filter(id=1).count() == 1
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_success.status_code == 302
        assert (
            response_success.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response_success.status_code == 403


@pytest.mark.django_db
def test_upload_file(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_upload_file")

    with open(
        os.getcwd()
        + "/integreat_cms/static/src/logos/aschaffenburg/aschaffenburg-logo.png",
        "rb",
    ) as file:
        uploaded_file = SimpleUploadedFile(
            "file", file.read(), content_type="image/png"
        )
        response = client.post(
            url,
            {
                "parent_directory": 1,
                "file": uploaded_file,
            },
            format="multipart",
        )

    if role in PRIV_STAFF_ROLES:
        assert response.status_code == 200
        # Check that the file was uploaded
        assert MediaFile.objects.filter(name="file").count() == 1
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_replace_file(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_replace_file")

    with open(
        os.getcwd()
        + "/integreat_cms/static/src/logos/aschaffenburg/aschaffenburg-logo.png",
        "rb",
    ) as file:
        uploaded_file = SimpleUploadedFile(
            "file_replaced", file.read(), content_type="image/png"
        )
        response = client.post(
            url,
            {"id": 1, "file": uploaded_file},
            format="multipart",
        )

    if role in PRIV_STAFF_ROLES:
        assert response.status_code == 200
        # Check the file was replaced
        assert MediaFile.objects.filter(id=1).first().name == "file_replaced"
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_edit_file(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_edit_file")

    # Test with unchanged input
    response_without_change = client.post(
        url,
        data={
            "id": 2,
            "name": "Test Logo 2",
            "alt_text": "alt text",
            "is_hidden": False,
        },
    )
    # Test with changed input
    response_with_change = client.post(
        url,
        data={
            "id": 2,
            "name": "New name",
            "alt_text": "new alt text",
            "is_hidden": False,
        },
    )

    if role in PRIV_STAFF_ROLES:
        assert response_without_change.status_code == 200
        assert response_with_change.status_code == 200
        # Check that the file was renamed
        assert MediaFile.objects.filter(id=2).first().name == "New name"
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_without_change.status_code == 302
        assert response_with_change.status_code == 302
        assert (
            response_without_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
        assert (
            response_with_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response_without_change.status_code == 403
        assert response_with_change.status_code == 403


@pytest.mark.django_db
def test_move_file(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_move_file")

    # Test with unchanged input
    response_without_change = client.post(
        url,
        data={
            "mediafile_id": 1,
            "parent_directory": 1,
        },
    )
    # Test with changed input
    response_with_change = client.post(
        url,
        data={
            "mediafile_id": 2,
            "parent_directory": 1,
        },
    )

    if role in PRIV_STAFF_ROLES:
        assert response_without_change.status_code == 200
        assert response_with_change.status_code == 200
        # Check that the file was moved
        assert MediaFile.objects.filter(id=2).first().parent_directory.id == 1
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_without_change.status_code == 302
        assert response_with_change.status_code == 302
        assert (
            response_without_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
        assert (
            response_with_change.headers.get("location")
            == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response_without_change.status_code == 403
        assert response_with_change.status_code == 403


@pytest.mark.django_db
def test_delete_file(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    next_url = url = reverse("mediacenter_delete_file")

    response = client.post(url, data={"id": 2})

    if role in PRIV_STAFF_ROLES:
        assert response.status_code == 200
        # Check that the file was deleted
        assert not MediaFile.objects.filter(id=2).count()
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_get_file_usages(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    query = parse.urlencode(
        {
            "file": 1,
        }
    )
    next_url = reverse("mediacenter_get_file_usages")
    url = f"{next_url}?{query}"

    response = client.get(url)

    if role in STAFF_ROLES:
        assert response.status_code == 200
        # Check contents in the response
        assert "Test Organization" in response.content.decode("utf-8")
        assert not "Welcome" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_get_search_result(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    query = parse.urlencode(
        {
            "query": "test",
        }
    )
    next_url = reverse("mediacenter_get_search_result")
    url = f"{next_url}?{query}"

    response = client.get(url)

    if role in STAFF_ROLES:
        assert response.status_code == 200
        # Check contents in the response
        assert "Test Directory" in response.content.decode("utf-8")
        assert "Test Logo" in response.content.decode("utf-8")
        assert not "Empty Directory" in response.content.decode("utf-8")

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403
