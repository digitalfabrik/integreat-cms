"""
Test Chat API / Zammad

As we have no Zammad server in the test setup, we need to mock the responses.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.models import ABTester, Language, Region, UserChat

if TYPE_CHECKING:
    from django.http import HttpResponse

default_kwargs = {
    "region_slug": "augsburg",
    "language_slug": "de",
    "device_id": "exampleDeviceID",
}


def mark_chat_active(device_id: str) -> None:
    """
    Update the current chat's ``last_message_timestamp`` to now so it is not
    considered expired. Uses a queryset update to bypass the ``auto_now`` behaviour.

    :param device_id: device id whose current chat should be marked active
    """
    current = UserChat.objects.current_chat(device_id)
    UserChat.objects.filter(pk=current.pk).update(last_message_timestamp=timezone.now())


def mark_chat_expired(device_id: str) -> None:
    """
    Update the current chat's ``last_message_timestamp`` to be older than the
    retention period so it is considered expired. Uses a queryset update to bypass
    the ``auto_now`` behaviour.

    :param device_id: device id whose current chat should be marked expired
    """
    current = UserChat.objects.current_chat(device_id)
    expired_timestamp = timezone.now() - timedelta(
        days=settings.INTEGREAT_CHAT_TICKET_RETENTION_DAYS + 1
    )
    UserChat.objects.filter(pk=current.pk).update(
        last_message_timestamp=expired_timestamp
    )


@pytest.mark.django_db
def test_api_is_chat_enabled_for_user(load_test_data: None) -> None:
    """
    Check that whether a user is chat beta tester is stored in the DB

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:is_chat_enabled_for_user",
        kwargs={"region_slug": "augsburg", "device_id": "ab_tester"},
    )
    response = client.get(url)
    db_entry = ABTester.objects.filter(device_id="ab_tester").first()

    assert db_entry is not None
    assert response.status_code == 200
    assert response.json() == {"is_chat_enabled": db_entry.is_tester}


@pytest.mark.django_db
@patch("integreat_cms.api.v3.chat.user_chat.UserChat.zammad_request")
def test_api_chat_missing_auth_error(
    zammad_request: Mock, load_test_data: None
) -> None:
    """
    Check that missing/wrong auth information leads to an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])

    myerror = requests.exceptions.HTTPError()
    myerror.status_code = 403  # type: ignore[attr-defined]
    zammad_request.side_effect = myerror

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.get(url)

    assert response.status_code == 500
    assert response.json() == {
        "error": "An error occurred while attempting to connect to the chat server."
    }


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.Region.zammad_url",
    return_value="https://zammad.example.com",
)
def test_api_chat_incorrect_server_error(
    mock_zammad_url: Mock,
    load_test_data: None,
) -> None:
    """
    Check that incorrect server url leads to an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])
    cache.delete("api_rate_limit_127.0.0.1")
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.get(url)

    assert response.status_code == 500
    assert response.json() == {
        "error": "An error occurred while attempting to connect to the chat server.",
    }


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    new=Mock(return_value=True),
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch("integreat_cms.api.v3.chat.user_chat.UserChat.create_ticket", return_value=111)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 2, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question",
    return_value=True,
)
def test_api_chat_first_chat(
    automatic_answers: Mock,
    get_zammad_user_mail: Mock,
    create_ticket: Mock,
    evaluation_consent: Mock,
    save_message: Mock,
    messages: Mock,
    celery_translate_and_answer_question: Mock,
    load_test_data: None,
) -> None:
    """
    Check that sending a message from a never seen-before device_id creates a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs | {"device_id": "never_seen_before"},
    )
    response = client.post(url, data={"message": "test message"})

    create_ticket.assert_called_once()
    save_message.assert_called_once()
    assert response.status_code == 200
    assert UserChat.objects.current_chat("never_seen_before").zammad_id == 111
    assert UserChat.objects.current_chat("never_seen_before").processing_answer


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    new=Mock(return_value=True),
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 1, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question",
    return_value=lambda: True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_language_slug",
    return_value=True,
)
def test_api_chat_set_evaluation_consent(
    save_language_slug: Mock,
    celery_translate_and_answer_question: Mock,
    evaluation_consent: Mock,
    save_message: Mock,
    save_evaluation_consent: Mock,
    messages: Mock,
    get_zammad_user_mail: Mock,
    automatic_answers: Mock,
    load_test_data: None,
) -> None:
    """
    Check that setting evaluation consent works for an existing (active) chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])

    client = Client()
    url = reverse("api:chat", kwargs=default_kwargs)
    response = client.post(
        url, data={"message": "test message", "evaluation_consent": True}
    )

    assert response.status_code == 200
    save_message.assert_called_once()
    save_evaluation_consent.assert_called_once()


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    return_value=False,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 1, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_language_slug",
    return_value=True,
)
def test_api_chat_send_message(
    save_language_slug: Mock,
    celery_translate_and_answer_question: Mock,
    get_zammad_user_mail: Mock,
    save_message: Mock,
    get_messages: Mock,
    evaluation_consent: Mock,
    automatic_answers: Mock,
    last_message_is_internal_note: Mock,
    load_test_data: None,
) -> None:
    """
    Check that sending a message with a known device_id works and does not create a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])
    previous_chat = UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.post(url, data={"message": "test message"})

    assert response.status_code == 200
    assert response.json()["chatbot_typing"]
    assert (
        UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id
        == previous_chat
    )
    assert UserChat.objects.current_chat(default_kwargs["device_id"]).processing_answer


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    new=Mock(return_value=True),
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 1, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch("integreat_cms.api.v3.chat.user_chat.celery_translate_question")
@patch("integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question")
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_language_slug",
    return_value=True,
)
def test_api_chat_send_internal_note(
    save_language_slug: Mock,
    celery_translate_and_answer_question: Mock,
    celery_translate_question: Mock,
    get_zammad_user_mail: Mock,
    save_message: Mock,
    get_messages: Mock,
    evaluation_consent: Mock,
    automatic_answers: Mock,
    load_test_data: None,
) -> None:
    """
    Post-ing with ``internal=true`` is saved as an internal note

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])
    cache.delete(f"generating_answer_{default_kwargs['device_id']}")
    cache.delete("api_rate_limit_127.0.0.1")

    response = Client().post(
        reverse("api:chat", kwargs=default_kwargs),
        data={"message": "Test internal", "internal": "true"},
    )

    assert response.status_code == 200
    save_message.assert_called_once_with(
        message="Test internal", internal=True, automatic_message=False
    )
    celery_translate_and_answer_question.apply_async.assert_not_called()
    celery_translate_question.apply_async.assert_not_called()
    assert not response.json()["chatbot_typing"]
    assert response.json()["last_message_is_internal_note"]


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    return_value=False,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 1, "updated_at": "2025-11-13T21:49+01:00"},
)
def test_api_chat_get_messages_success(
    save_message: Mock,
    evaluation_consent: Mock,
    messages: Mock,
    get_zammad_user_mail: Mock,
    last_message_is_internal_note: Mock,
    load_test_data: None,
) -> None:
    """
    Check that GET-ing messages works for an existing chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    new=Mock(return_value=True),
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch("integreat_cms.api.v3.chat.user_chat.UserChat.create_ticket", return_value=222)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 222, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question",
    return_value=True,
)
def test_api_chat_stale_chat_starts_new_chat(
    celery_translate_and_answer_question: Mock,
    evaluation_consent: Mock,
    save_message: Mock,
    messages: Mock,
    create_ticket: Mock,
    get_zammad_user_mail: Mock,
    automatic_answers: Mock,
    load_test_data: None,
) -> None:
    """
    Check that a new chat is started when the existing chat has been inactive long
    enough that its Zammad ticket is assumed to be gone (Zammad's retention policy).

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    previous_chat = UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id
    # Mark the existing chat as inactive beyond the retention period
    mark_chat_expired(default_kwargs["device_id"])

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.post(url, data={"message": "test message"})

    assert response.status_code == 200
    # A new ticket should have been created for the same device id
    create_ticket.assert_called_once()
    current_chat = UserChat.objects.current_chat(default_kwargs["device_id"])
    assert current_chat.zammad_id == 222
    assert current_chat.zammad_id != previous_chat


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
def test_api_chat_stale_chat_get_returns_not_found(
    get_zammad_user_mail: Mock,
    load_test_data: None,
) -> None:
    """
    Check that GET-ing messages for an expired chat returns a "not found" error
    instead of creating a new chat.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_expired(default_kwargs["device_id"])

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.get(url)

    assert response.status_code == 404
    assert response.json() == {
        "error": "Chat not found.",
    }


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
def test_api_chat_get_messages_failure(
    get_zammad_user_mail: Mock, load_test_data: None
) -> None:
    """
    Check that GET-ing messages for a non-existing chat returns an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs | {"device_id": "nonexistent"},
    )
    response = client.get(url)

    assert response.status_code == 404
    assert response.json() == {
        "error": "Chat not found.",
    }


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    return_value=False,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value=True,
)
def test_api_chat_ratelimiting(
    save_message: Mock,
    evaluation_consent: Mock,
    messages: Mock,
    get_zammad_user_mail: Mock,
    last_message_is_internal_note: Mock,
    load_test_data: None,
) -> None:
    """
    Check that the ratelimiting correctly prevents further API requests

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])
    cache.delete("api_rate_limit_127.0.0.1")
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )

    # request #0 (we don't count the first chat creation)
    client.post(url, data={"message": "is it ham?"})

    # requests #1 through #LIMIT-1
    for _ in range(settings.API_RATE_LIMIT_WINDOW - 2):
        client.get(url)

    # requests #LIMIT and #LIMIT+1
    response_ok = client.get(url)
    response_err = client.get(url)

    assert response_ok.status_code == 200
    assert response_err.status_code == 429
    assert response_err.json() == {
        "error": "Too many requests. Please try again later."
    }

    # make sure ratelimiting cannot be circumvented by force-creating new chats
    response_force = client.post(
        url,
        data={"message": "no, it's spam.", "force_new": True},
    )
    assert response_force.status_code == 429


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    return_value=False,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value=True,
)
@override_settings(TRUSTED_IP_HEADER="HTTP_X_FORWARDED_FOR")
def test_api_chat_ratelimiting_trusted_ip_header(
    save_message: Mock,
    evaluation_consent: Mock,
    messages: Mock,
    get_zammad_user_mail: Mock,
    last_message_is_internal_note: Mock,
    load_test_data: None,
) -> None:
    """
    Check that ratelimiting kicks in when a trusted IP header is configured but not set in the request.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mark_chat_active(default_kwargs["device_id"])
    cache.delete("api_rate_limit_127.0.0.1")
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )

    client.post(url, data={"message": "is it spam?"})
    response = client.get(url)
    assert response.status_code == 429
    assert response.json() == {"error": "Too many requests. Please try again later."}

    client = Client()
    client.post(url, data={"message": "is it ham?"})
    response = client.get(url, HTTP_X_FORWARDED_FOR="10.0.0.2")
    assert response.status_code == 200


def zammad_webhook_payload(ticket: dict) -> dict:
    """
    Build a minimal Zammad webhook payload for a human counselor answer

    :param ticket: ticket attributes of the payload
    :return: webhook payload
    """
    return {
        "ticket": {"automatic_answers": False} | ticket,
        "article": {
            "body": "counselor answer",
            "internal": False,
            "sender": "Agent",
            "created_by": {"login": "counselor@example.com"},
        },
    }


def post_zammad_webhook(token: str, payload: dict) -> HttpResponse:
    """
    Send a Zammad webhook request

    :param token: webhook token of the region
    :param payload: webhook payload
    :return: response of the webhook view
    """
    return Client().post(
        f"{reverse('api:zammad_webhook')}?token={token}",
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("other_zammad_url", "expected_status"),
    [("https://zammad.example.com", 200), ("https://other-zammad.example.com", 404)],
)
@patch("integreat_cms.api.v3.chat.user_chat.celery_translate_answer")
def test_zammad_webhook_shared_zammad(
    celery_translate_answer: Mock,
    load_test_data: None,
    other_zammad_url: str,
    expected_status: int,
) -> None:
    """
    Check that a webhook sent with the token of one region finds chats of other
    regions using the same Zammad server, but not chats of regions with their own server.

    :param celery_translate_answer: Mocked translation task
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param other_zammad_url: Zammad URL of the second region
    :param expected_status: expected HTTP status of the webhook response
    """
    token_region = Region.objects.get(slug="augsburg")
    other_region = Region.objects.get(slug="nurnberg")
    other_region.zammad_url = other_zammad_url
    other_region.integreat_chat_enabled = True
    other_region.save()
    UserChat(
        region=other_region,
        device_id="nurnbergDeviceID",
        zammad_id=5,
        language=other_region.default_language,
    ).save()

    response = post_zammad_webhook(
        str(token_region.zammad_webhook_token), zammad_webhook_payload({"id": 5})
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["region"] == "nurnberg"
        celery_translate_answer.apply_async.assert_called_once()
    else:
        celery_translate_answer.apply_async.assert_not_called()


@pytest.mark.django_db
@patch("integreat_cms.api.v3.chat.user_chat.celery_translate_answer")
def test_zammad_webhook_device_with_multiple_chats(
    celery_translate_answer: Mock,
    load_test_data: None,
) -> None:
    """
    Check that a webhook finds the correct chat if the device has multiple chats.
    Tickets created with the former ``MULTI_REGION_ZAMMAD`` setting still contain
    a device_id attribute, which has to be ignored.

    :param celery_translate_answer: Mocked translation task
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    region = Region.objects.get(slug="augsburg")
    UserChat(
        region=region,
        device_id=default_kwargs["device_id"],
        zammad_id=6,
        language=region.default_language,
    ).save()

    response = post_zammad_webhook(
        str(region.zammad_webhook_token),
        zammad_webhook_payload({"id": 6, "device_id": default_kwargs["device_id"]}),
    )

    assert response.status_code == 200
    celery_translate_answer.apply_async.assert_called_once()
    assert celery_translate_answer.apply_async.call_args.kwargs["args"][2] == 6


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch("integreat_cms.api.v3.chat.user_chat.UserChat.zammad_request")
def test_create_ticket_contains_region_and_language_slug(
    zammad_request: Mock,
    get_zammad_user_mail: Mock,
    load_test_data: None,
) -> None:
    """
    Check that new Zammad tickets contain the region and language slugs, which can be used
    in Zammad triggers of shared Zammad servers

    :param zammad_request: Mocked Zammad API request
    :param get_zammad_user_mail: Mocked Zammad user mail
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    zammad_request.return_value.json.return_value = {"id": 7}
    region = Region.objects.get(slug="augsburg")

    chat = UserChat.objects.create(
        region=region, device_id="newDeviceID", language=region.default_language
    )

    assert chat.zammad_id == 7
    method, path, payload = zammad_request.call_args.args
    assert (method, path) == ("POST", "/api/v1/tickets")
    assert payload["region_slug"] == "augsburg"
    assert payload["language_slug"] == region.default_language.slug


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("previous_language_slug", "language_changed"), [("en", True), ("de", False)]
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.last_message_is_internal_note",
    return_value=False,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.automatic_answers",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value={"ticket_id": 1, "updated_at": "2025-11-13T21:49+01:00"},
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_language_slug",
    return_value=True,
)
@patch("integreat_cms.api.v3.chat.user_chat.celery_translate_and_answer_question")
def test_api_chat_language_change_updates_ticket(
    celery_translate_and_answer_question: Mock,
    save_language_slug: Mock,
    save_message: Mock,
    evaluation_consent: Mock,
    get_messages: Mock,
    automatic_answers: Mock,
    last_message_is_internal_note: Mock,
    load_test_data: None,
    previous_language_slug: str,
    language_changed: bool,
) -> None:
    """
    Check that the language slug of the Zammad ticket is only updated if the
    app user changed the language

    :param celery_translate_and_answer_question: Mocked answering task
    :param save_language_slug: Mocked update of the Zammad ticket language
    :param save_message: Mocked saving of the message
    :param evaluation_consent: Mocked evaluation consent
    :param get_messages: Mocked chat messages
    :param automatic_answers: Mocked automatic answers flag
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param previous_language_slug: language of the chat before the message
    :param language_changed: whether the ticket language should be updated
    """
    mark_chat_active(default_kwargs["device_id"])
    UserChat.objects.filter(device_id=default_kwargs["device_id"]).update(
        language=Language.objects.get(slug=previous_language_slug)
    )

    response = Client().post(
        reverse("api:chat", kwargs=default_kwargs), data={"message": "test message"}
    )

    assert response.status_code == 200
    assert save_language_slug.called == language_changed
    assert (
        UserChat.objects.current_chat(default_kwargs["device_id"]).language.slug
        == default_kwargs["language_slug"]
    )
