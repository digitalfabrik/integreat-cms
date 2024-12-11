import pytest
from _pytest.logging import LogCaptureFixture
from django.test.client import Client
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.constants import translation_status
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from tests.conftest import PRIV_STAFF_ROLES
from tests.utils import assert_message_in_log, assert_no_error_messages, get_messages

success_messages = {
    translation_status.UP_TO_DATE: 'SUCCESS  Page "test_translation_title" was not in translation process.',
    translation_status.IN_TRANSLATION: 'SUCCESS  Translation process was successfully cancelled for page "test_translation_title".',
}


@pytest.mark.django_db
@pytest.mark.parametrize("login_role_user", PRIV_STAFF_ROLES, indirect=True)  # Rollen
@pytest.mark.parametrize("page_ids", [[30, 31]])
def test_page_bulk_actions(
    load_test_data: None,
    page_ids: list[int],
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    settings: SettingsWrapper,
) -> None:

    client, _ = login_role_user

    # Test for english messages
    settings.LANGUAGE_CODE = "en"

    # store the previous translation state for each page
    prev_status = {}
    for page_id in page_ids:
        translation = PageTranslation.objects.get(page__id=page_id)
        prev_status[page_id] = translation.translation_state

    # call the cancellation routine
    kwargs = {"region_slug": "nurnberg", "language_slug": "de"}
    cancel_translation_process = reverse("cancel_translation_process", kwargs=kwargs)
    response = client.post(
        cancel_translation_process, data={"selected_ids[]": page_ids}
    )

    # confirm that the response is a redirect
    assert response.status_code == 302

    # confirm that no errors were generated
    assert_no_error_messages(caplog)

    # get all other log messages
    messages = get_messages(caplog)

    # confirm that the number of logs corresponds to the number of pages
    assert len(messages) == len(page_ids)

    # confirm the expected parameters for individual pages
    for page_id in page_ids:

        # get the pagetranslation object for this page
        translation = PageTranslation.objects.get(page__id=page_id)

        # confirm that the page is not in translation, regardless of the initial state
        assert translation.translation_state != translation_status.IN_TRANSLATION

        assert_message_in_log(
            success_messages[prev_status[page_id]].replace(
                "test_translation_title", translation.title
            ),
            caplog,
        )
