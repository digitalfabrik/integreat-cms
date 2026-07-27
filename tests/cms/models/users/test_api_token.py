from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from integreat_cms.cms.models import ApiToken

if TYPE_CHECKING:
    from typing import Any

    from django.test.client import Client


@pytest.mark.django_db
def test_create_token_does_not_store_plaintext(load_test_data: None) -> None:
    """
    The plaintext token must never be persisted — only its hash.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    user = get_user_model().objects.get(username="root")
    token, plaintext = ApiToken.create_token(user, "CRM")

    assert token.token_hash != plaintext
    assert plaintext not in token.token_hash
    assert token.prefix == plaintext.partition(".")[0]
    assert ApiToken.objects.filter(token_hash=plaintext).count() == 0


@pytest.mark.django_db
def test_get_by_token(load_test_data: None) -> None:
    """
    A token can be resolved by its plaintext, and unknown or malformed tokens resolve to ``None``.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    user = get_user_model().objects.get(username="root")
    token, plaintext = ApiToken.create_token(user, "CRM")

    assert ApiToken.get_by_token(plaintext) == token
    # Correct prefix, wrong secret
    assert ApiToken.get_by_token(f"{token.prefix}.wrong-secret") is None
    # Unknown prefix
    assert ApiToken.get_by_token("unknown.secret") is None
    # Malformed token without separator
    assert ApiToken.get_by_token("no-separator") is None
    assert ApiToken.get_by_token("") is None


@pytest.mark.django_db
def test_plaintext_is_not_logged_via_messages(
    load_test_data: None,
    settings: Any,
    client: Client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Creating a token must not write the plaintext into the log.

    :class:`~integreat_cms.core.storages.MessageLoggerStorage` logs every message of the messages
    framework, so the plaintext has to be handed over via the session instead.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param settings: The Django settings
    :param client: The Django test client
    :param caplog: The pytest log capture fixture
    """
    settings.MESSAGE_LOGGING_ENABLED = True
    client.force_login(get_user_model().objects.get(username="root"))

    with caplog.at_level(logging.DEBUG):
        response = client.post(
            reverse("user_settings"),
            {"submit_form": "api_token_form", "name": "CRM"},
        )

    assert response.status_code == 302
    plaintext = client.session["new_api_token"]
    assert plaintext
    assert ApiToken.objects.filter(user__username="root", name="CRM").exists()
    assert plaintext not in caplog.text
