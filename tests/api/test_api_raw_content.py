from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import pytest
from django.core.cache import cache
from django.test.client import Client

from integreat_cms.cms.models import (
    Language,
    PushNotification,
    PushNotificationTranslation,
    Region,
)

from .api_config import API_RAW_CONTENT_ENDPOINTS

#: The region and language which are used for the tests which are not parametrized
REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"


def _create_push_notification(
    sent_date: datetime | None, text: str = "body"
) -> PushNotificationTranslation:
    """
    Create a push notification in :attr:`REGION_SLUG` whose translation is in :attr:`LANGUAGE_SLUG`.

    :param sent_date: The date the push notification was sent, or ``None`` if it has not been sent yet
    :param text: The text of the push notification translation

    :return: The translation of the created push notification
    """
    push_notification = PushNotification.objects.create(
        channel="news",
        sent_date=sent_date,
        created_date=datetime.now(tz=UTC),
        scheduled_send_date=None,
    )
    push_notification.regions.add(Region.objects.get(slug=REGION_SLUG))
    return PushNotificationTranslation.objects.create(
        title="Aktuelle Nachricht",
        text=text,
        language=Language.objects.get(slug=LANGUAGE_SLUG),
        push_notification=push_notification,
        last_updated=datetime.now(tz=UTC),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,expected_result,expected_code,expected_queries",
    API_RAW_CONTENT_ENDPOINTS,
)
def test_api_result(
    load_test_data: None,
    django_assert_num_queries: Callable,
    endpoint: str,
    expected_result: str,
    expected_code: int,
    expected_queries: int,
) -> None:
    """
    This test class checks all endpoints defined in :attr:`~tests.api.api_config.API_RAW_CONTENT_ENDPOINTS`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding html file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_assert_num_queries: The fixture providing the query assertion
    :param endpoint: The url of the new Django pattern
    :param expected_result: The path to the html file that contains the expected result
    :param expected_code: The expected HTTP status code
    :param expected_queries: The expected number of SQL queries
    """
    client = Client()
    with django_assert_num_queries(expected_queries):
        response = client.get(endpoint, format="html")
    assert response.status_code == expected_code
    with open(expected_result, encoding="utf-8") as f:
        assert f.read() == response.content.decode("utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("prefix", ["/api/v3/raw-content", "/api/v3/social"])
def test_local_news_is_addressed_by_translation_id(
    load_test_data: None, prefix: str
) -> None:
    """
    Local news are addressed by the id of their translation, just like in the web app and in the news API.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param prefix: The url prefix of the endpoint under test
    """
    pn_translation = _create_push_notification(datetime.now(tz=UTC) - timedelta(days=1))

    response = Client().get(
        f"{prefix}/{REGION_SLUG}/{LANGUAGE_SLUG}/news/local/{pn_translation.id}/"
    )

    assert response.status_code == 200
    assert "Aktuelle Nachricht" in response.content.decode("utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("prefix", ["/api/v3/raw-content", "/api/v3/social"])
@pytest.mark.parametrize(
    "sent_date",
    [None, datetime(2022, 3, 5, tzinfo=UTC)],
    ids=["unsent", "expired"],
)
def test_local_news_which_is_not_public(
    load_test_data: None, prefix: str, sent_date: datetime | None
) -> None:
    """
    Local news which have not been sent yet or which are older than the FCM history window are not exposed.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param prefix: The url prefix of the endpoint under test
    :param sent_date: The date the push notification was sent, or ``None`` if it has not been sent yet
    """
    pn_translation = _create_push_notification(sent_date, text="Geheimer Inhalt")

    response = Client().get(
        f"{prefix}/{REGION_SLUG}/{LANGUAGE_SLUG}/news/local/{pn_translation.id}/"
    )

    assert response.status_code == 404
    assert "Geheimer Inhalt" not in response.content.decode("utf-8")


@pytest.mark.django_db
def test_local_news_text_is_escaped(load_test_data: None) -> None:
    """
    The text of a push notification is plain text, so it must be escaped and its line breaks must be kept.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    pn_translation = _create_push_notification(
        datetime.now(tz=UTC) - timedelta(days=1),
        text="Erste Zeile\nZweite Zeile <script>alert(1)</script>",
    )

    response = Client().get(
        f"/api/v3/raw-content/{REGION_SLUG}/{LANGUAGE_SLUG}/news/local/{pn_translation.id}/"
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "<script>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert "Erste Zeile<br>Zweite Zeile" in content


@pytest.mark.django_db
def test_external_news_content_is_sanitized(
    load_test_data: None, clean_news_cache: None
) -> None:
    """
    External news are not created in our own editor, so their content must be sanitized before it is served.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param clean_news_cache: Fixture that wipes external news-source cache entries
    """
    now = datetime.now(tz=UTC)
    cache.set(
        f"tunews:{LANGUAGE_SLUG}",
        [
            {
                "id": "tunews-42",
                "title": "Tü News Post",
                "content": "<p>Tü News</p><script>alert(1)</script>",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "tunews",
                "externalUrl": "https://dummy.com",
            }
        ],
        timeout=None,
    )

    response = Client().get(
        f"/api/v3/raw-content/{REGION_SLUG}/{LANGUAGE_SLUG}/news/tunews/42/"
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "<p>Tü News</p>" in content
    assert "alert(1)" not in content
