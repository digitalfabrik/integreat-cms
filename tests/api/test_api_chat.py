"""
Test Chat API / Zammad

As we have no Zammad server in the test setup, we need to mock the responses.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from django.core.cache import cache
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import ABTester, UserChat

default_kwargs = {
    "region_slug": "augsburg",
    "language_slug": "de",
    "device_id": "exampleDeviceID",
}


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
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch("integreat_cms.api.v3.chat.user_chat.UserChat.create_ticket", return_value=111)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
def test_api_chat_first_chat(
    evaluation_consent: Mock,
    save_message: Mock,
    messages: Mock,
    create_ticket: Mock,
    get_zammad_user_mail: Mock,
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


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_evaluation_consent",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
def test_api_chat_set_evaluation_consent(
    evaluation_consent: Mock,
    save_message: Mock,
    save_evaluation_consent: Mock,
    messages: Mock,
    get_zammad_user_mail: Mock,
    load_test_data: None,
) -> None:
    """
    Check that sending a message from a never seen-before device_id creates a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
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
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.save_message",
    return_value=True,
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.messages",
    return_value=[{"body": "message1", "user_is_author": True}],
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.evaluation_consent",
    return_value=True,
)
def test_api_chat_send_message(
    evaluation_consent: Mock,
    messages: Mock,
    save_message: Mock,
    get_zammad_user_mail: Mock,
    load_test_data: None,
) -> None:
    """
    Check that sending a message with a known device_id works and does not create a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    previous_chat = UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id

    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.post(url, data={"message": "test message"})

    assert response.status_code == 200
    assert (
        UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id
        == previous_chat
    )


@pytest.mark.django_db
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.get_zammad_user_mail",
    return_value="tech@tuerantuer.org",
)
@patch(
    "integreat_cms.api.v3.chat.user_chat.UserChat.messages",
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
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )
    response = client.get(url)

    assert response.status_code == 200


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
    "integreat_cms.api.v3.chat.user_chat.UserChat.messages",
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
    cache.delete("chat_rate_limit_127.0.0.1")
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs,
    )

    # request #0 (we don't count the first chat creation)
    client.post(url, data={"message": "is it ham?"})

    # requests #1 through #LIMIT-1
    for _ in range(settings.USER_CHAT_WINDOW_LIMIT - 2):
        client.get(url)

    # requests #LIMIT and #LIMIT+1
    response_ok = client.get(url)
    response_err = client.get(url)

    assert response_ok.status_code == 200
    assert response_err.status_code == 429
    assert response_err.json() == {"error": "Too many requests."}

    # make sure ratelimiting cannot be circumvented by force-creating new chats
    response_force = client.post(
        url,
        data={"message": "no, it's spam.", "force_new": True},
    )
    assert response_force.status_code == 429
