from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from requests.exceptions import HTTPError

from integreat_cms.cms.models import AttachmentMap, UserChat

default_kwargs = {
    "region_slug": "augsburg",
    "language_slug": "de",
    "device_id": "exampleDeviceID",
}


@pytest.mark.django_db
def test_api_is_chat_enabled_true(load_test_data: None) -> None:
    """
    Check that regions with enabled chat return true

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:is_chat_enabled",
        kwargs={"region_slug": "augsburg"},
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {"is_chat_enabled": True}


@pytest.mark.django_db
def test_api_is_chat_enabled_false(load_test_data: None) -> None:
    """
    Check that regions without enabled chat return false

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:is_chat_enabled",
        kwargs={"region_slug": "artland"},
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {"is_chat_enabled": False}


@pytest.mark.django_db
def test_api_chat_missing_auth_error(load_test_data: None) -> None:
    """
    Check that missing auth information leads to an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    client = Client()
    url = reverse(
        "api:chat",
        kwargs=default_kwargs | {"region_slug": "artland"},
    )
    response = client.get(url)

    assert response.status_code == 503
    assert response.json() == {"error": "No chat server is configured for your region."}


@pytest.mark.django_db
def test_api_chat_incorrect_auth_error(load_test_data: None) -> None:
    """
    Check that incorrect auth information leads to an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.me.side_effect = HTTPError()

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
def test_api_chat_first_chat(load_test_data: None) -> None:
    """
    Check that sending a message from a never seen-before device_id creates a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket.create.return_value = {"id": 111}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs | {"device_id": "never_seen_before"},
        )
        response = client.post(url, data={"message": "test message"})

        assert response.status_code == 200
        assert UserChat.objects.current_chat("never_seen_before").zammad_id == 111


@pytest.mark.django_db
def test_api_chat_force_new_chat(load_test_data: None) -> None:
    """
    Check that sending a message with force_new creates a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket.create.return_value = {"id": 222}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs,
        )
        response = client.post(url, data={"message": "test message", "force_new": True})

        assert response.status_code == 200
        assert (
            UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id == 222
        )


@pytest.mark.django_db
def test_api_chat_send_message(load_test_data: None) -> None:
    """
    Check that sending a message with a known device_id works and does not create a new chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    previous_chat = UserChat.objects.current_chat(default_kwargs["device_id"]).zammad_id
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket_article.create.return_value = {}

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
def test_api_chat_get_messages_success(load_test_data: None) -> None:
    """
    Check that GET-ing messages works for an existing chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket.articles.return_value = []

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs,
        )
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
def test_api_chat_get_messages_failure(load_test_data: None) -> None:
    """
    Check that GET-ing messages for a non-existing chat returns an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs | {"device_id": "nonexistent"},
        )
        response = client.get(url)

        assert response.status_code == 404
        assert response.json() == {
            "error": "The requested chat does not exist. Did you delete it?"
        }


@pytest.mark.django_db
def test_api_chat_create_attachment_success(load_test_data: None) -> None:
    """
    Check that getting a chat containing an attachement creates the mapping in the database

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket.articles.return_value = [
            {
                "id": 444,
                "body": "message",
                "user_is_author": False,
                "attachments": [
                    {
                        "id": 10,
                        "filename": "sample.pdf",
                        "size": "41412",
                        "preferences": {"Content-Type": "application/pdf"},
                    }
                ],
            },
        ]

        client = Client()
        url = reverse("api:chat", kwargs=default_kwargs)

        response = client.get(url)
        random_hash = json.loads(response.content.decode("utf-8"))["messages"][0][
            "attachments"
        ][0]["id"]

        assert response.status_code == 200
        assert AttachmentMap.objects.get(random_hash=random_hash)


@pytest.mark.django_db
def test_api_chat_get_attachment_success(load_test_data: None) -> None:
    """
    Check that getting an attachment works for an existing chat

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket_article_attachment.download.return_value = b"\00"

        client = Client()
        url = reverse("api:chat", kwargs=default_kwargs)

        response = client.get(url)

        url = reverse(
            "api:chat", kwargs=default_kwargs | {"attachment_id": "exampleRandomHash"}
        )
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
def test_api_chat_get_attachment_incorrect_chat_failure(load_test_data: None) -> None:
    """
    Check that getting an attachment for a non-existing chat returns an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs
            | {
                "device_id": "doesNotOwnTheAttachment",
                "attachment_id": "exampleRandomHash",
            },
        )
        response = client.get(url)

        assert response.status_code == 404
        assert response.json() == {"error": "The requested attachment does not exist."}


@pytest.mark.django_db
def test_api_chat_get_attachment_missing_attachment_failure(
    load_test_data: None,
) -> None:
    """
    Check that getting an attachment for a non-existing attachment_id returns an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs | {"attachment_id": "nonexistent"},
        )
        response = client.get(url)

        assert response.status_code == 404
        assert response.json() == {"error": "The requested attachment does not exist."}


@pytest.mark.django_db
def test_api_chat_ratelimiting(load_test_data: None) -> None:
    """
    Check that the ratelimiting correctly prevents further API requests

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    mock_api = MagicMock()
    with patch("integreat_cms.api.v3.chat.zammad_api.ZammadAPI", return_value=mock_api):
        mock_api.user.all.return_value = []
        mock_api.user.me.return_value = {"login": "bot-user"}
        mock_api.ticket.create.return_value = {"id": 333}

        client = Client()
        url = reverse(
            "api:chat",
            kwargs=default_kwargs | {"device_id": "spammer"},
        )

        # request #0 (we don't count the first chat creation)
        client.post(url, data={"message": "is it ham?"})

        # requests #1 through #LIMIT-1
        for _ in range(settings.USER_CHAT_WINDOW_LIMIT - 1):
            client.get(url)

        # requests #LIMIT and #LIMIT+1
        response_ok = client.get(url)
        response_err = client.get(url)

        assert response_ok.status_code == 200
        assert response_err.status_code == 429
        assert response_err.json() == {"error": "You're doing that too often."}

        # make sure ratelimiting cannot be circumvented by force-creating new chats
        response_force = client.post(
            url, data={"message": "no, it's spam.", "force_new": True}
        )
        assert response_force.status_code == 429
