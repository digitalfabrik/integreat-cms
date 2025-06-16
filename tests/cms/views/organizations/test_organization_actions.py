from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.urls import reverse

from integreat_cms.cms.models import Organization
from tests.conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES, MANAGEMENT
from tests.utils import assert_message_in_log

REGION_SLUG = "augsburg"

REFERENCED_ORGANIZATION_ID = 1
NOT_REFERENCED_ORGANIZATION_ID = 3
ARCHIVED_ORGANIZATION_ID = 2

test_archive_parameters = [
    (REFERENCED_ORGANIZATION_ID, False),
    (NOT_REFERENCED_ORGANIZATION_ID, True),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", test_archive_parameters)
def test_archive_organization(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[int, bool],
) -> None:
    """
    Test whether archiving an organization is working as expected
    """
    client, role = login_role_user
    organization_id, should_be_archived = parameter

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    archive_organization = reverse(
        "archive_organization",
        kwargs={
            "organization_id": organization_id,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(archive_organization)

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302

        redirect_url = response.headers.get("location")

        if should_be_archived:
            assert_message_in_log(
                "SUCCESS  Organization was successfully archived",
                caplog,
            )
            assert "Organization was successfully archived" in client.get(
                redirect_url,
            ).content.decode("utf-8")
            assert Organization.objects.filter(id=organization_id).first().archived
        else:
            assert_message_in_log(
                "ERROR    Organization couldn't be archived as it's used by a page, poi or user",
                caplog,
            )
            assert (
                "Organization couldn&#x27;t be archived as it&#x27;s used by a page, poi or user"
                in client.get(redirect_url).content.decode("utf-8")
            )
            assert not Organization.objects.filter(id=organization_id).first().archived

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_organization}"
        )
    else:
        assert response.status_code == 403


test_delete_parameters = [
    (REFERENCED_ORGANIZATION_ID, False),
    (NOT_REFERENCED_ORGANIZATION_ID, True),
    (ARCHIVED_ORGANIZATION_ID, True),
]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", test_delete_parameters)
def test_delete_organization(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[int, bool],
) -> None:
    """
    Test whether deleting an organization is working as expected
    """
    client, role = login_role_user
    organization_id, should_be_deleted = parameter

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    delete_organization = reverse(
        "delete_organization",
        kwargs={
            "organization_id": organization_id,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(delete_organization)

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302

        redirect_url = response.headers.get("location")

        if should_be_deleted:
            assert_message_in_log(
                "SUCCESS  Organization was successfully deleted",
                caplog,
            )
            assert "Organization was successfully deleted" in client.get(
                redirect_url,
            ).content.decode("utf-8")
            assert not Organization.objects.filter(id=organization_id).first()
        else:
            assert_message_in_log(
                "ERROR    Organization couldn't be deleted as it's used by a page, poi or user",
                caplog,
            )
            assert (
                "Organization couldn&#x27;t be deleted as it&#x27;s used by a page, poi or user"
                in client.get(redirect_url).content.decode("utf-8")
            )
            assert Organization.objects.filter(id=organization_id).first()

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_organization}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_restore_organization(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether restoring an organization is working as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    archived_organization = Organization.objects.filter(
        region__slug=REGION_SLUG,
        archived=True,
    ).first()
    assert archived_organization

    archived_organization_id = archived_organization.id

    restore_organization = reverse(
        "restore_organization",
        kwargs={
            "organization_id": archived_organization_id,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(restore_organization)

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        assert_message_in_log(
            "SUCCESS  Organization was successfully restored",
            caplog,
        )
        assert "Organization was successfully restored" in client.get(
            redirect_url,
        ).content.decode("utf-8")
        assert (
            not Organization.objects.filter(id=archived_organization_id)
            .first()
            .archived
        )

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={restore_organization}"
        )
    else:
        assert response.status_code == 403


BULK_ARCHIVE_SELECTED_IDS = [REFERENCED_ORGANIZATION_ID, NOT_REFERENCED_ORGANIZATION_ID]


@pytest.mark.django_db
def test_bulk_archive_organizations(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk archiving of organizations is working as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    bulk_archive_organization = reverse(
        "bulk_archive_organization",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_archive_organization,
        data={"selected_ids[]": BULK_ARCHIVE_SELECTED_IDS},
    )

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")

        assert_message_in_log(
            "ERROR    Organization \"Nicht archivierte Organisation\" couldn't be archived as it's used by a page, poi or user.",
            caplog,
        )
        assert (
            "Organization &quot;Nicht archivierte Organisation&quot; couldn&#x27;t be archived as it&#x27;s used by a page, poi or user."
            in redirect_page
        )
        assert (
            not Organization.objects.filter(id=REFERENCED_ORGANIZATION_ID)
            .first()
            .archived
        )
        assert_message_in_log(
            'SUCCESS  Organization "Not Referenced Organisation" was successfully archived.',
            caplog,
        )
        assert (
            "Organization &quot;Not Referenced Organisation&quot; was successfully archived."
            in redirect_page
        )
        assert (
            Organization.objects.filter(id=NOT_REFERENCED_ORGANIZATION_ID)
            .first()
            .archived
        )
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_archive_organization}"
        )
    else:
        assert response.status_code == 403


BULK_DELETE_SELECTED_IDS = [REFERENCED_ORGANIZATION_ID, NOT_REFERENCED_ORGANIZATION_ID]


@pytest.mark.django_db
def test_bulk_delete_organizations(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk deleting of organizations is working as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    bulk_delete_organization = reverse(
        "bulk_delete_organization",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_delete_organization,
        data={"selected_ids[]": BULK_DELETE_SELECTED_IDS},
    )

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")

        assert_message_in_log(
            "ERROR    Organization \"Nicht archivierte Organisation\" couldn't be deleted as it's used by a page, poi or user.",
            caplog,
        )
        assert (
            "Organization &quot;Nicht archivierte Organisation&quot; couldn&#x27;t be deleted as it&#x27;s used by a page, poi or user."
            in redirect_page
        )
        assert Organization.objects.filter(id=REFERENCED_ORGANIZATION_ID).exists()
        assert_message_in_log(
            'SUCCESS  Organization "Not Referenced Organisation" was successfully deleted.',
            caplog,
        )
        assert (
            "Organization &quot;Not Referenced Organisation&quot; was successfully deleted."
            in redirect_page
        )
        assert not Organization.objects.filter(
            id=NOT_REFERENCED_ORGANIZATION_ID,
        ).exists()
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_delete_organization}"
        )
    else:
        assert response.status_code == 403


BULK_RESTORE_SELECTED_IDS = [ARCHIVED_ORGANIZATION_ID]


@pytest.mark.django_db
def test_bulk_restore_organizations(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk restoring of organizations is working as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    bulk_restore_organization = reverse(
        "bulk_restore_organization",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_restore_organization,
        data={"selected_ids[]": BULK_RESTORE_SELECTED_IDS},
    )

    if role in [*HIGH_PRIV_STAFF_ROLES, MANAGEMENT]:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")

        assert_message_in_log(
            'SUCCESS  Organization "Archivierte Organisation" was successfully restored.',
            caplog,
        )
        assert (
            "Organization &quot;Archivierte Organisation&quot; was successfully restored."
            in redirect_page
        )
        assert (
            not Organization.objects.filter(id=ARCHIVED_ORGANIZATION_ID)
            .first()
            .archived
        )
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_restore_organization}"
        )
    else:
        assert response.status_code == 403
