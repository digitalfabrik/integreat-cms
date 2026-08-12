from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TypedDict

import requests
from django.conf import settings
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
        per_page = 100
        oldest_date = (
            datetime.now() - timedelta(days=settings.TUNEWS_HISTORY_DAYS)
        ).isoformat()

        for language in Language.objects.all():
            news = []
            page_count = 1
            import_failed = False
            while True:
                try:
                    response = requests.get(
                        f"https://tuenews.de/wp-json/wp/v2/posts/?lang={language.slug}&per_page={per_page}&page={page_count}&after={oldest_date}",
                        timeout=10,
                    )
                except requests.exceptions.RequestException:
                    logger.exception(
                        "Failed to fetch posts from TuNews in %s.", language
                    )
                    import_failed = True
                    break

                result = response.json()
                if response.status_code != 200:
                    code = result.get("code")
                    if code == "rest_invalid_param" and "lang" in result.get(
                        "data", {}
                    ).get("params", {}):
                        # Language genuinely not served by Tü News, not a failure:
                        # cache the (empty) result to avoid retrying import at every request.
                        logger.debug(
                            "Tü News does not serve %s; caching empty result.", language
                        )
                    elif code == "rest_post_invalid_page_number":
                        # No more pages, not a failure: keep the posts gathered so far.
                        logger.debug("Reached end of pagination for %s.", language)
                    else:
                        logger.error(
                            "Could not fetch page %s in %s.", page_count, language
                        )
                        import_failed = True
                    break

                logger.info(
                    "Got %s result in %s.",
                    len(result),
                    language,
                )
                for post in result:
                    try:
                        if not post["acf"]["integreat"]:
                            continue
                        news.append(self.transform_post(post))
                    except (KeyError, TypeError, ValueError):
                        logger.exception(
                            "Malformed Tü News post (id=%s); skipped.",
                            post.get("id"),
                        )

                if len(result) < per_page:
                    break
                page_count += 1

            if not import_failed:
                cache.set(f"{self.short_name}:{language.slug}", news, timeout=None)
                logger.info(
                    "Saved %s news in %s",
                    len(cache.get(f"{self.short_name}:{language.slug}")),
                    language,
                )

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
            "published_at": date,
            "display_date": date,
            "channel": None,
            "available_languages": None,
            "source": self.short_name,
            "externalUrl": post["link"],
        }
