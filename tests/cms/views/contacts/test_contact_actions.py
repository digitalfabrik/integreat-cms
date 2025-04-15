from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.urls import reverse

from integreat_cms.cms.models import Contact
from tests.conftest import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
)
from tests.utils import assert_message_in_log

# Use the region Augsburg, as it has some contacts in the test data
REGION_SLUG = "augsburg"

USED_CONTACT_ID = 5
NOT_USED_CONTACT_ID = 3
ARCHIVED_CONTACT_ID = 2


test_archive_parameters = [(NOT_USED_CONTACT_ID, True), (USED_CONTACT_ID, False)]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", test_archive_parameters)
@pytest.mark.django_db
def test_archive_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[int, bool],
) -> None:
    """
    Test that archiving a contact works as expected
    """
    client, role = login_role_user
    contact_id, should_be_archived = parameter

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    contact_string = str(Contact.objects.filter(id=contact_id).first())

    archive_contact = reverse(
        "archive_contact",
        kwargs={
            "contact_id": contact_id,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(archive_contact)

    if role in (*HIGH_PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        if should_be_archived:
            assert_message_in_log(
                f"SUCCESS  Contact {contact_string} was successfully archived",
                caplog,
            )
            assert f"Contact {contact_string} was successfully archived" in client.get(
                redirect_url,
            ).content.decode("utf-8")
            assert Contact.objects.filter(id=contact_id).first().archived
        else:
            assert_message_in_log(
                f'ERROR    Cannot archive contact "{contact_string}" while content objects refer to it.',
                caplog,
            )
            assert (
                f"Cannot archive contact &quot;{contact_string}&quot; while content objects refer to it."
                in client.get(redirect_url).content.decode("utf-8")
            )
            assert not Contact.objects.filter(id=contact_id).first().archived
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={archive_contact}"
        )
    else:
        assert response.status_code == 403


test_delete_parameters = [(NOT_USED_CONTACT_ID, True), (USED_CONTACT_ID, False)]


@pytest.mark.django_db
@pytest.mark.parametrize("parameter", test_delete_parameters)
@pytest.mark.django_db
def test_delete_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    parameter: tuple[int, bool],
) -> None:
    """
    Test that deleting a contact works as expected
    """
    client, role = login_role_user
    contact_id, should_be_deleted = parameter

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    contact_string = str(Contact.objects.filter(id=contact_id).first())

    delete_contact = reverse(
        "delete_contact",
        kwargs={
            "contact_id": contact_id,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(delete_contact)

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        if should_be_deleted:
            assert_message_in_log(
                f"SUCCESS  Contact {contact_string} was successfully deleted",
                caplog,
            )
            assert f"Contact {contact_string} was successfully deleted" in client.get(
                redirect_url,
            ).content.decode("utf-8")
            assert not Contact.objects.filter(id=contact_id).first()
        else:
            assert_message_in_log(
                f'ERROR    Cannot delete contact "{contact_string}" while content objects refer to it.',
                caplog,
            )
            assert (
                f"Cannot delete contact &quot;{contact_string}&quot; while content objects refer to it."
                in client.get(redirect_url).content.decode("utf-8")
            )
            assert Contact.objects.filter(id=contact_id).first()
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_contact}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_restore_contact(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether restoring a contact works as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    archived_contact = Contact.objects.filter(id=ARCHIVED_CONTACT_ID).first()
    assert archived_contact.archived

    contact_string = str(archived_contact)

    restore_contact = reverse(
        "restore_contact",
        kwargs={
            "contact_id": ARCHIVED_CONTACT_ID,
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(restore_contact)

    if role in (*HIGH_PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        assert_message_in_log(
            f"SUCCESS  Contact {contact_string} was successfully restored",
            caplog,
        )
        assert f"Contact {contact_string} was successfully restored" in client.get(
            redirect_url,
        ).content.decode("utf-8")
        assert not Contact.objects.filter(id=ARCHIVED_CONTACT_ID).first().archived

    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={restore_contact}"
        )
    else:
        assert response.status_code == 403


BULK_ARCHIVE_SELECTED_IDS = [NOT_USED_CONTACT_ID, USED_CONTACT_ID]


@pytest.mark.django_db
def test_bulk_archive_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk archiving of contacts works as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    not_used_contact_string = str(
        Contact.objects.filter(id=NOT_USED_CONTACT_ID).first(),
    )
    used_contact_string = str(Contact.objects.filter(id=USED_CONTACT_ID).first())

    bulk_archive_contacts = reverse(
        "bulk_archive_contacts",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_archive_contacts,
        data={"selected_ids[]": BULK_ARCHIVE_SELECTED_IDS},
    )

    if role in (*HIGH_PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")
        assert_message_in_log(
            f'ERROR    Contact "{used_contact_string}" cannot be archived while content objects refer to it.',
            caplog,
        )
        assert (
            f"Contact &quot;{used_contact_string}&quot; cannot be archived while content objects refer to it."
            in redirect_page
        )
        assert not Contact.objects.filter(id=USED_CONTACT_ID).first().archived
        assert_message_in_log(
            f'SUCCESS  Contact "{not_used_contact_string}" was successfully archived.',
            caplog,
        )
        assert (
            f"Contact &quot;{not_used_contact_string}&quot; was successfully archived."
            in redirect_page
        )
        assert Contact.objects.filter(id=NOT_USED_CONTACT_ID).first().archived
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_archive_contacts}"
        )
    else:
        assert response.status_code == 403


BULK_DELETE_SELECTED_IDS = [NOT_USED_CONTACT_ID, USED_CONTACT_ID]


@pytest.mark.django_db
def test_bulk_delete_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk deleting of contacts works as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    not_used_contact_string = str(
        Contact.objects.filter(id=NOT_USED_CONTACT_ID).first(),
    )
    used_contact_string = str(Contact.objects.filter(id=USED_CONTACT_ID).first())

    bulk_delete_contacts = reverse(
        "bulk_delete_contacts",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_delete_contacts,
        data={"selected_ids[]": BULK_DELETE_SELECTED_IDS},
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")
        assert_message_in_log(
            f'ERROR    Contact "{used_contact_string}" cannot be deleted while content objects refer to it.',
            caplog,
        )
        assert (
            f"Contact &quot;{used_contact_string}&quot; cannot be deleted while content objects refer to it."
            in redirect_page
        )
        assert Contact.objects.filter(id=USED_CONTACT_ID).first()
        assert_message_in_log(
            f'SUCCESS  Contact "{not_used_contact_string}" was successfully deleted.',
            caplog,
        )
        assert (
            f"Contact &quot;{not_used_contact_string}&quot; was successfully deleted."
            in redirect_page
        )
        assert not Contact.objects.filter(id=NOT_USED_CONTACT_ID).first()
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_delete_contacts}"
        )
    else:
        assert response.status_code == 403


BULK_RESTORE_SELECTED_IDS = [ARCHIVED_CONTACT_ID]


@pytest.mark.django_db
def test_bulk_restore_contacts(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
) -> None:
    """
    Test whether bulk restoring of contacts works as expected
    """
    client, role = login_role_user

    # Set the language setting to English so assertion does not fail because of corresponding German sentence appearing instead the english one.
    settings.LANGUAGE_CODE = "en"

    contact_string = str(Contact.objects.filter(id=ARCHIVED_CONTACT_ID).first())

    bulk_restore_contacts = reverse(
        "bulk_restore_contacts",
        kwargs={
            "region_slug": REGION_SLUG,
        },
    )
    response = client.post(
        bulk_restore_contacts,
        data={"selected_ids[]": BULK_RESTORE_SELECTED_IDS},
    )

    if role in (*HIGH_PRIV_STAFF_ROLES, MANAGEMENT, EDITOR, AUTHOR):
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        redirect_page = client.get(redirect_url).content.decode("utf-8")

        assert_message_in_log(
            f'SUCCESS  Contact "{contact_string}" was successfully restored.',
            caplog,
        )
        assert (
            f"Contact &quot;{contact_string}&quot; was successfully restored."
            in redirect_page
        )
        assert not Contact.objects.filter(id=ARCHIVED_CONTACT_ID).first().archived
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={bulk_restore_contacts}"
        )
    else:
        assert response.status_code == 403
