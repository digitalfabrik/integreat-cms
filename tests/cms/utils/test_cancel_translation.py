from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from _pytest.logging import LogCaptureFixture
from django.test.client import Client
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.constants import translation_status
from integreat_cms.cms.models import Page
from tests.conftest import ANONYMOUS, AUTHOR, EDITOR, MANAGEMENT, PRIV_STAFF_ROLES
from tests.utils import assert_message_in_log

IDS_PAGES_NOT_IN_TRANSLATION_PROCESS = [1, 2]
IDS_PAGES_IN_TRANSLATION_PROCESS = [32, 33]
LANGUAGE_SLUG = "en"
REGION_SLUG = "augsburg"


@pytest.mark.django_db
def test_bulk_cancel_translation_process(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:
    client, role = login_role_user

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    for page_id in IDS_PAGES_IN_TRANSLATION_PROCESS:
        assert (
            Page.objects.filter(id=page_id).first().get_translation_state(LANGUAGE_SLUG)
            == translation_status.IN_TRANSLATION
        )
    for page_id in IDS_PAGES_NOT_IN_TRANSLATION_PROCESS:
        assert (
            not Page.objects.filter(id=page_id)
            .first()
            .get_translation_state(LANGUAGE_SLUG)
            == translation_status.IN_TRANSLATION
        )

    kwargs = {"region_slug": REGION_SLUG, "language_slug": LANGUAGE_SLUG}
    combined_page_ids = (
        IDS_PAGES_IN_TRANSLATION_PROCESS + IDS_PAGES_NOT_IN_TRANSLATION_PROCESS
    )
    cancel_translation_process = reverse("cancel_translation_process", kwargs=kwargs)
    response = client.post(
        cancel_translation_process, data={"selected_ids[]": combined_page_ids}
    )

    if role in PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR]:
        assert response.status_code == 302
        redirect_url = response.headers.get("location")
        response = client.get(redirect_url)
        assert (
            "The following pages were not in translation process: &quot;Welcome&quot; and &quot;Willkommen in Augsburg&quot;"
            in response.content.decode("utf-8")
        )
        assert_message_in_log(
            'SUCCESS  The following pages were not in translation process: "Welcome" and "Willkommen in Augsburg"',
            caplog,
        )
        assert (
            "Translation process was successfully cancelled for the following pages: &quot;This is currently in translation!&quot; and &quot;This is currently in translation 2&quot;"
            in response.content.decode("utf-8")
        )
        assert_message_in_log(
            'SUCCESS  Translation process was successfully cancelled for the following pages: "This is currently in translation!" and "This is currently in translation 2"',
            caplog,
        )
        for page_id in combined_page_ids:
            assert (
                not Page.objects.filter(id=page_id)
                .first()
                .get_translation_state(LANGUAGE_SLUG)
                == translation_status.IN_TRANSLATION
            )
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={cancel_translation_process}"
        )
    else:
        assert response.status_code == 403
