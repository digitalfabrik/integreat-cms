from __future__ import annotations

from datetime import datetime, timedelta, UTC

import pytest
from django.core.cache import cache
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import (
    Language,
    PushNotification,
    PushNotificationTranslation,
    Region,
)


def _create_push_notification(
    region_slug: str, language_slug: str, sent_date: datetime
) -> int:
    """
    Create a push notification in ``region_slug`` whose translation is in
    ``language_slug`` and whose ``sent_date`` is the given datetime. Returns
    the id of the translation (which is what the API exposes as ``id``).
    """
    region = Region.objects.get(slug=region_slug)
    language = Language.objects.get(slug=language_slug)
    push_notification = PushNotification.objects.create(
        channel="news",
        sent_date=sent_date,
        created_date=sent_date,
        scheduled_send_date=None,
    )
    push_notification.regions.add(region)
    push_notification.save()
    translation = PushNotificationTranslation.objects.create(
        title="title",
        text="body",
        language=language,
        push_notification=push_notification,
        last_updated=sent_date,
    )
    return translation.id


@pytest.mark.django_db
def test_news_endpoint(load_test_data: None, clean_news_cache: None) -> None:
    """
    The combined endpoint merges items from every news source and sorts them
    by ``display_date``, newest first.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param clean_news_cache: Fixture that wipes external news-source cache entries
    """
    region_slug = "augsburg"
    language_slug = "de"
    url = reverse(
        "api:news",
        kwargs={"region_slug": region_slug, "language_slug": language_slug},
    )
    client = Client()

    # Future timestamps so our items dominate the sort regardless of fixture
    # state — we can assert their relative positions without needing to know
    # what already exists.
    now = datetime.now(tz=UTC)
    pn_high_time = now + timedelta(hours=3)
    tunews_time = now + timedelta(hours=2)
    pn_low_time = now + timedelta(hours=1)

    tunews_id = 42
    cache.set(
        f"tunews:{language_slug}",
        [
            {
                "id": tunews_id,
                "title": "Tü News Post",
                "message": "Tü News",
                "timestamp": tunews_time,
                "last_updated": tunews_time,
                "display_date": tunews_time,
                "channel": None,
                "available_languages": None,
                "source": "tuNews",
                "link": "https://dummy.com",
            }
        ],
        timeout=None,
    )

    pn_high_id = _create_push_notification(region_slug, language_slug, pn_high_time)
    pn_low_id = _create_push_notification(region_slug, language_slug, pn_low_time)

    result = client.get(url).json()
    top_ids = [item["id"] for item in result[:3]]

    assert top_ids == [pn_high_id, tunews_id, pn_low_id]


@pytest.mark.django_db
def test_news_endpoint_pagination(load_test_data: None, clean_news_cache: None) -> None:
    """
    The combined endpoint returns only one page of results at a time.
    Page 1 contains the most recent items; page 2 contains the next batch.
    Non-integer and out-of-range page numbers fall back gracefully via
    :func:`~integreat_cms.cms.views.mixins.get_safe_page`.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param clean_news_cache: Fixture that wipes external news-source cache entries
    """
    region_slug = "augsburg"
    language_slug = "de"
    url = reverse(
        "api:news",
        kwargs={"region_slug": region_slug, "language_slug": language_slug},
    )
    client = Client()

    now = datetime.now(tz=UTC)
    # Create 3 push notifications with descending timestamps
    ids = [
        _create_push_notification(
            region_slug, language_slug, now + timedelta(hours=3 - i)
        )
        for i in range(3)
    ]

    # Page 1 with size 2 — exactly the two most recent items
    result_page1 = client.get(url, {"page": 1, "size": 2}).json()
    assert len(result_page1) == 2
    assert [item["id"] for item in result_page1] == ids[:2]

    # Page 2 with size 2 — contains the third item, and none of page 1's items
    result_page2 = client.get(url, {"page": 2, "size": 2}).json()
    page2_ids = [item["id"] for item in result_page2]
    assert ids[2] in page2_ids
    assert ids[0] not in page2_ids
    assert ids[1] not in page2_ids

    # Non-integer page falls back to page 1
    result_bad_page = client.get(url, {"page": "abc", "size": 2}).json()
    assert [item["id"] for item in result_bad_page] == ids[:2]

    # Out-of-range page falls back to the last (non-empty) page
    response_overflow = client.get(url, {"page": 9999, "size": 2})
    assert response_overflow.status_code == 200
    assert response_overflow.json()


@pytest.mark.django_db
def test_news_endpoint_source_filter(
    load_test_data: None, clean_news_cache: None
) -> None:
    """
    The combined endpoint supports filtering by source.
    Filtering by ``local`` returns only push notifications;
    filtering by ``tunews`` returns only tüNews items.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param clean_news_cache: Fixture that wipes external news-source cache entries
    """
    region_slug = "augsburg"
    language_slug = "de"
    url = reverse(
        "api:news",
        kwargs={"region_slug": region_slug, "language_slug": language_slug},
    )
    client = Client()

    now = datetime.now(tz=UTC)
    tunews_id = 99
    cache.set(
        f"tunews:{language_slug}",
        [
            {
                "id": tunews_id,
                "title": "Tü News Post",
                "message": "Tü News",
                "timestamp": now,
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "tuNews",
                "link": "https://dummy.com",
            }
        ],
        timeout=None,
    )
    pn_id = _create_push_notification(region_slug, language_slug, now)

    # Filter by local — only push notifications
    local_result = client.get(url, {"source": "local"}).json()
    assert all(item["source"] == "local" for item in local_result)
    assert any(item["id"] == pn_id for item in local_result)
    assert not any(item["id"] == tunews_id for item in local_result)

    # Filter by tunews — only tüNews items
    tunews_result = client.get(url, {"source": "tuNews"}).json()
    assert all(item["source"] == "tuNews" for item in tunews_result)
    assert any(item["id"] == tunews_id for item in tunews_result)
    assert not any(item["id"] == pn_id for item in tunews_result)

    # Multi-valued filter — both sources together (?source=local&source=tuNews)
    both_result = client.get(url, {"source": ["local", "tuNews"]}).json()
    assert {item["source"] for item in both_result} == {"local", "tuNews"}
    assert any(item["id"] == pn_id for item in both_result)
    assert any(item["id"] == tunews_id for item in both_result)
