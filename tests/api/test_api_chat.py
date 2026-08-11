"""
Test Chat API / Zammad

As we have no Zammad server in the test setup, we need to mock the responses.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.models import ABTester, UserChat

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
def test_api_chat_set_evaluation_consent(
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
def test_api_chat_send_message(
    celery_translate_and_answer_question: Mock,
    get_zammad_user_mail: Mock,
    save_message: Mock,
    get_messages: Mock,
    evaluation_consent: Mock,
    automatic_answers: Mock,
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
