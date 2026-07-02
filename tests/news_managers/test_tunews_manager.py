from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import patch

import pytest
from django.core.cache import cache

from integreat_cms.news_managers.tunews_manager import clean_html, TunewsManager

not_integreat_news = {
    "id": 1,
    "date": "2026-04-29T16:58:38",
    "link": "https://tuenews.de/news-post-1/",
    "title": {"rendered": "Titel der Nachricht 1"},
    "content": {"rendered": "Eine interessante Tatsache", "protected": False},
    "acf": {
        "integreat": False,
    },
}

malformed_news_1 = {
    "id": 2,
    "date": "2026-04-29T16:58:38",
    "link": "https://tuenews.de/news-post-2/",
    "title": {"rendered": "Kaputte Nachricht 1"},
    "content": {"rendered": "Eine interessante Tatsache", "protected": False},
}
malformed_news_2 = {
    "id": 3,
    "date": "2026-04-29T16:58:38",
    "link": "https://tuenews.de/news-post-3/",
    "title": {"rendered": "Kaputte Nachricht 2"},
    "acf": {
        "integreat": True,
    },
}
valid_news = {
    "id": 4,
    "date": "2026-04-29T16:58:38",
    "link": "https://tuenews.de/news-post-4/",
    "title": {"rendered": "Gültige Nachricht"},
    "content": {"rendered": "Eine interessante Tatsache", "protected": False},
    "acf": {
        "integreat": True,
    },
}
expected_result = [
    {
        "id": "tuNews-4",
        "title": "Gültige Nachricht",
        "content": "<main>Eine interessante Tatsache</main>\n",
        "last_updated": datetime(2026, 4, 29, 16, 58, 38, tzinfo=UTC),
        "display_date": datetime(2026, 4, 29, 16, 58, 38, tzinfo=UTC),
        "channel": None,
        "available_languages": None,
        "source": "tuNews",
        "externalUrl": "https://tuenews.de/news-post-4/",
    }
]

dummy_news_items = [not_integreat_news, malformed_news_1, malformed_news_2, valid_news]


@pytest.mark.django_db
def test_import_news_item(load_test_data: None, clean_news_cache: None) -> None:
    with patch(
        "integreat_cms.news_managers.tunews_manager.requests.get"
    ) as fake_tunews_server:
        fake_tunews_server.return_value.status_code = 200
        fake_tunews_server.return_value.json.return_value = dummy_news_items

        assert not cache.get("tunews:de")

        TunewsManager().import_news_items()

        assert cache.get("tunews:de") == expected_result


def test_clean_html_keeps_plain_text() -> None:
    assert clean_html("Eine interessante Tatsache") == (
        "<main>Eine interessante Tatsache</main>\n"
    )


def test_clean_html_strips_pvc_elements() -> None:
    html = (
        "<p>Wichtig</p>"
        '<div class="pvc_stats_post">Counter</div>'
        '<span class="pvc_extra">x</span>'
    )
    result = clean_html(html)
    assert "pvc_" not in result
    assert "Counter" not in result
    assert "Wichtig" in result


def test_clean_html_preserves_unrelated_classes() -> None:
    html = '<p class="intro">Hallo</p><p class="pvc_x">Weg</p>'
    result = clean_html(html)
    assert 'class="intro"' in result
    assert "Hallo" in result
    assert "Weg" not in result
