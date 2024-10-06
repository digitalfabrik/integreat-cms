import pytest
from _pytest.logging import LogCaptureFixture

from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.constants import translation_status
from tests.conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES
from tests.utils import get_messages, assert_no_error_messages

success_messages = {
    translation_status.UP_TO_DATE: [
        'SUCCESS  Seite "test_translation_title" war nicht im Übersetzungsprozess',
        'SUCCESS  Page "test_translation_title" was not in translation process.',
    ],
    translation_status.IN_TRANSLATION: [
        'SUCCESS  Der Übersetzungsprozess für Seite "test_translation_title" wurde erfolgreich abgebrochen.',
        'SUCCESS  Translation process was successfully cancelled for page "test_translation_title".',
    ],
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True  # Rollen
)
@pytest.mark.parametrize("page_ids", [[30, 31]])
def test_page_bulk_actions(
    load_test_data: None,
    page_ids: list[int],
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
) -> None:

    client, _ = login_role_user

    prev_status = {}
    for page_id in page_ids:
        translation = PageTranslation.objects.get(page__id=page_id)
        prev_status[page_id] = translation.translation_state

    kwargs = {"region_slug": "augsburg", "language_slug": "de"}
    cancel_translation_process = reverse("cancel_translation_process", kwargs=kwargs)
    response = client.post(
        cancel_translation_process, data={"selected_ids[]": page_ids}
    )
    assert response.status_code == 302

    assert_no_error_messages(caplog)

    messages = get_messages(caplog)
    assert len(messages) == len(page_ids)

    for page_id in page_ids:
        translation = PageTranslation.objects.get(page__id=page_id)
        assert translation.translation_state != translation_status.IN_TRANSLATION

        target_messages = [
            msg.replace("test_translation_title", translation.title)
            for msg in success_messages[prev_status[page_id]]
        ]

        # check if one at least one of the larget messages could be found in the caplog
        assert any(msg in messages for msg in target_messages)
