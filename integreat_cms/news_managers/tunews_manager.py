from __future__ import annotations

import logging
from datetime import datetime
from typing import TypedDict

import requests
from django.core.cache import cache

from ..cms.models import Language
from .abstract_news_manager import AbstractNewsManager, clean_html, NewsItem

logger = logging.getLogger(__name__)


class _TunewsRenderedField(TypedDict):
    rendered: str


class _TunewsACF(TypedDict):
    integreat: bool


class _TunewsPost(TypedDict):
    """
    The subset of fields we rely on from the upstream Tü News WordPress API.
    """

    id: int
    date: str
    link: str
    title: _TunewsRenderedField
    content: _TunewsRenderedField
    acf: _TunewsACF


class TunewsManager(AbstractNewsManager):
    short_name = "tunews"
    name = "Tü News"

    def import_news_items(self) -> None:
        """
        Imports Tü News posts and save them as cache
        """
        for language in Language.objects.all():
            try:
                response = requests.get(
                    f"https://tuenews.de/wp-json/wp/v2/posts/?lang={language.slug}",
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
                        if not post["acf"]["integreat"]:
                            continue
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
                    logger.info(
                        "Saved %s news in %s",
                        len(cache.get(f"{self.short_name}:{language.slug}")),
                        language,
                    )
                    for post in cache.get(f"{self.short_name}:{language.slug}"):
                        logger.info(post.get("title"))

            except requests.exceptions.RequestException:
                logger.exception("Failed to fetch posts in %s.", language)

    def transform_post(self, post: _TunewsPost) -> NewsItem:
        """
        Transforms a post of Tü News so it can be used by the news endpoint directly
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
