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
def test_news_endpoint(
    load_test_data: None, clean_news_cache: None, disable_auto_news_reimport: None
) -> None:
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
    pn_high_time = now + timedelta(hours=4)
    amalnews_time = now + timedelta(hours=3)
    tunews_time = now + timedelta(hours=2)
    pn_low_time = now + timedelta(hours=1)

    amalnews_id = "amalnews-42"
    cache.set(
        f"amalnews:{language_slug}",
        [
            {
                "id": amalnews_id,
                "title": "Amal News Post",
                "content": "Amal News",
                "last_updated": amalnews_time,
                "display_date": amalnews_time,
                "channel": None,
                "available_languages": None,
                "source": "amalnews",
                "externalUrl": "https://dummydummy.com",
            }
        ],
        timeout=None,
    )

    tunews_id = "tunews-42"
    cache.set(
        f"tunews:{language_slug}",
        [
            {
                "id": tunews_id,
                "title": "Tü News Post",
                "content": "Tü News",
                "last_updated": tunews_time,
                "display_date": tunews_time,
                "channel": None,
                "available_languages": None,
                "source": "tunews",
                "externalUrl": "https://dummy.com",
            }
        ],
        timeout=None,
    )

    pn_high_id = (
        f"local-{_create_push_notification(region_slug, language_slug, pn_high_time)}"
    )
    pn_low_id = (
        f"local-{_create_push_notification(region_slug, language_slug, pn_low_time)}"
    )

    result = client.get(url).json()
    top_ids = [item["id"] for item in result[:4]]

    assert top_ids == [pn_high_id, amalnews_id, tunews_id, pn_low_id]


@pytest.mark.django_db
def test_news_endpoint_pagination(
    load_test_data: None, clean_news_cache: None, disable_auto_news_reimport: None
) -> None:
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
        f"local-{_create_push_notification(region_slug, language_slug, now + timedelta(hours=3 - i))}"
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
    load_test_data: None, clean_news_cache: None, disable_auto_news_reimport: None
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

    tunews_id = "tunews-99"
    cache.set(
        f"tunews:{language_slug}",
        [
            {
                "id": tunews_id,
                "title": "Tü News Post",
                "content": "Tü News",
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

    amalnews_id = "amalnews-99"
    cache.set(
        f"amalnews:{language_slug}",
        [
            {
                "id": amalnews_id,
                "title": "Amal News Post",
                "content": "Amal News",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "amalnews",
                "externalUrl": "https://dummydummy.com",
            }
        ],
        timeout=None,
    )

    pn_id = f"local-{_create_push_notification(region_slug, language_slug, now)}"

    # Filter by local — only push notifications
    local_result = client.get(url, {"source": "local"}).json()
    assert all(item["source"] == "local" for item in local_result)
    assert any(item["id"] == pn_id for item in local_result)
    assert not any(item["id"] == tunews_id for item in local_result)
    assert not any(item["id"] == amalnews_id for item in local_result)

    # Filter by tunews — only tüNews items
    tunews_result = client.get(url, {"source": "tunews"}).json()
    assert all(item["source"] == "tunews" for item in tunews_result)
    assert any(item["id"] == tunews_id for item in tunews_result)
    assert not any(item["id"] == pn_id for item in tunews_result)
    assert not any(item["id"] == amalnews_id for item in tunews_result)

    # Filter by amalnews — only amalnews items
    amalnews_result = client.get(url, {"source": "amalnews"}).json()
    assert all(item["source"] == "amalnews" for item in amalnews_result)
    assert any(item["id"] == amalnews_id for item in amalnews_result)
    assert not any(item["id"] == pn_id for item in amalnews_result)
    assert not any(item["id"] == tunews_id for item in amalnews_result)

    # Multi-valued filter — both sources together (?source=local&source=tunews)
    multi_source_result = client.get(url, {"source": ["local", "tunews"]}).json()
    assert {item["source"] for item in multi_source_result} == {"local", "tunews"}
    assert any(item["id"] == pn_id for item in multi_source_result)
    assert any(item["id"] == tunews_id for item in multi_source_result)
    assert not any(item["id"] == amalnews_id for item in multi_source_result)


@pytest.mark.django_db
def test_single_news_endpoint(
    load_test_data: None, clean_news_cache: None, disable_auto_news_reimport: None
) -> None:
    """
    The single news endpoint returns one news that matches the given id.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param clean_news_cache: Fixture that wipes external news-source cache entries
    """
    region_slug = "augsburg"
    language_slug = "de"

    client = Client()

    now = datetime.now(tz=UTC)

    tunews_id_1 = "tunews-1"
    tunews_id_2 = "tunews-2"
    tunews_id_non_existing = "tunews-42"
    cache.set(
        f"tunews:{language_slug}",
        [
            {
                "id": tunews_id_1,
                "title": "Tü News Post",
                "content": "Tü News",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "tunews",
                "externalUrl": "https://dummy.com",
            },
            {
                "id": tunews_id_2,
                "title": "Tü News Post",
                "content": "Tü News",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "tunews",
                "externalUrl": "https://dummy.com",
            },
        ],
        timeout=None,
    )

    pn_id_1 = f"local-{_create_push_notification(region_slug, language_slug, now)}"
    _create_push_notification(region_slug, language_slug, now)
    pn_id_non_existing = "local-0"

    amalnews_id_1 = "amalnews-1"
    amalnews_id_2 = "amalnews-2"
    amalnews_id_non_existing = "amalnews-42"
    cache.set(
        f"amalnews:{language_slug}",
        [
            {
                "id": amalnews_id_1,
                "title": "Amal News Post",
                "content": "Amal News",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "amalnews",
                "externalUrl": "https://dummydummy.com",
            },
            {
                "id": amalnews_id_2,
                "title": "Amal News Post",
                "content": "Amal News",
                "last_updated": now,
                "display_date": now,
                "channel": None,
                "available_languages": None,
                "source": "amalnews",
                "externalUrl": "https://dummydummy.com",
            },
        ],
        timeout=None,
    )

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": tunews_id_1,
        },
    )
    tunews_result = client.get(url).json()
    assert tunews_result["id"] == tunews_id_1

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": pn_id_1,
        },
    )
    local_result = client.get(url).json()
    assert local_result["id"] == pn_id_1

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": amalnews_id_1,
        },
    )
    amalnews_result = client.get(url).json()
    assert amalnews_result["id"] == amalnews_id_1

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": tunews_id_non_existing,
        },
    )
    tunews_result_non_existing = client.get(url).json()
    assert tunews_result_non_existing == {
        "error": "Tü News post not found in this region with this news ID."
    }

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": pn_id_non_existing,
        },
    )
    local_result_non_existing = client.get(url).json()
    assert local_result_non_existing == {
        "error": "Push Notification not found in this region with this language."
    }

    url = reverse(
        "api:single_news",
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            "news_id": amalnews_id_non_existing,
        },
    )
    amalnews_result_non_existing = client.get(url).json()
    assert amalnews_result_non_existing == {
        "error": "Amal News post not found in this region with this news ID."
    }
