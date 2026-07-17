from __future__ import annotations

import logging
from datetime import datetime
from typing import TypedDict

import requests
from django.core.cache import cache

from ..cms.models import Language
from .abstract_news_manager import AbstractNewsManager, clean_html, NewsItem

logger = logging.getLogger(__name__)


class _AmalnewsRenderedField(TypedDict):
    rendered: str


class _AmalnewsPost(TypedDict):
    """
    The subset of fields we rely on from the upstream Amal News WordPress API.
    """

    id: int
    date: str
    link: str
    title: _AmalnewsRenderedField
    content: _AmalnewsRenderedField


class AmalnewsManager(AbstractNewsManager):
    short_name = "amalnews"
    name = "Amal News"

    def import_news_items(self) -> None:
        """
        Imports Amal News posts and save them as cache
        """
        for language in Language.objects.all():
            # Amal News uses a non-standard slug for Ukrainian
            language_slug = language.slug if language.slug != "uk" else "ua"
            try:
                headers = {"User-Agent": ""}
                response = requests.get(
                    f"https://amalnews.de/wp-json/wp/v2/news?lang={language_slug}",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    logger.error(
                        "Could not find posts in %s.",
                        language,
                    )
                    continue

                posts = response.json()

                logger.info(
                    "Got %s posts in %s.",
                    len(posts),
                    language,
                )

                news = []

                for post in posts:
                    try:
                        news.append(self.transform_post(post))
                    except (KeyError, TypeError, ValueError):
                        logger.exception(
                            "Malformed %s post (id=%s); skipped.",
                            self.name,
                            post.get("id"),
                        )

                if news:
                    cache.set(f"{self.short_name}:{language.slug}", news, timeout=None)
                    logger.info("Saving %s news in %s", len(news), language)

            except requests.exceptions.RequestException:
                logger.exception("Failed to fetch posts in %s.", language)

    def transform_post(self, post: _AmalnewsPost) -> NewsItem:
        """
        Transforms a post of Amal News so it can be used by the news endpoint directly
        """
        date = datetime.fromisoformat(post["date"] + "+00:00")
        return {
            "id": f"{self.short_name}-{post['id']!s}",
            "title": post["title"]["rendered"],
            "content": clean_html(post["content"]["rendered"]),
            "last_updated": date,
            "display_date": date,
            "channel": None,
            "available_languages": None,
            "source": self.short_name,
            "externalUrl": post["link"],
        }
