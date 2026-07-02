from __future__ import annotations

import logging
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING, TypedDict

import requests
from django.core.cache import cache
from django.http import Http404, JsonResponse
from lxml import etree

from ..cms.models import Language, Region
from ..cms.utils.social_media_utils import render_social_media_headers
from .abstract_news_manager import AbstractNewsManager, NewsItem

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


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


def clean_html(html_string: str) -> str:
    """
    Remove unnecessary HTML elements from a Tü News post body.
    """
    root = etree.parse(  # noqa: S320
        StringIO("<main>" + html_string + "</main>"), etree.HTMLParser()
    )
    xpath_pvc = '//*[contains(@class, "pvc_")]'

    for pvc in root.xpath(xpath_pvc):
        pvc.getparent().remove(pvc)
    main = root.xpath("body/main")[0]

    return etree.tostring(main, pretty_print=True).decode("utf-8")


class TunewsManager(AbstractNewsManager):
    name = "tuNews"

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
                            "Malformed Tü News post (id=%s); skipped.",
                            post.get("id"),
                        )

                if news:
                    cache.set(f"tunews:{language.slug}", news, timeout=None)
                    logger.info("Saving %s news in %s", len(news), language)

            except requests.exceptions.RequestException:
                logger.exception("Failed to fetch posts in %s.", language)

    def collect_news_items(
        self, region_slug: str, language_slug: str, _channel: str
    ) -> list[NewsItem]:
        """
        Returns Tü News posts
        """
        posts = cache.get(f"tunews:{language_slug}", [])
        if not posts:
            return []
        try:
            if not Region.objects.get(slug=region_slug).external_news_enabled:
                return []
        except Region.DoesNotExist:
            logger.exception("Region not found: %s", region_slug)
            return []
        return posts

    def social_media_headers(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_raw_id: str,
    ) -> HttpResponse:
        """
        Tries rendering the social media headers for a news page in a specified region and language
        """
        post = self.find_post(region, language, news_raw_id)

        return render_social_media_headers(
            request=request,
            title=post["title"],
            language_code=language.bcp47_tag,
            excerpt=post["content"],
            url=post["externalUrl"],
        )

    def get_single_news(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_id: str,
    ) -> JsonResponse:
        """
        Returns a Tü News post that matches the id
        """
        post = self.find_post(region, language, news_id)
        return JsonResponse(post, safe=False)

    def find_post(
        self,
        region: Region,
        language: Language,
        news_raw_id: str,
    ) -> NewsItem:
        """
        Find and return a news item which matches the given ID
        """
        if not region.external_news_enabled:
            raise Http404("External news are not enabled in this region.")
        posts = cache.get(f"tunews:{language.slug}", [])
        post = next(
            (post for post in posts if post["id"] == f"{self.name}-{news_raw_id}"), None
        )

        if not post:
            raise Http404("Tü news post not found in this region with this news ID.")
        return post

    def transform_post(self, post: _TunewsPost) -> NewsItem:
        """
        Transforms a post of Tü News so it can be used by the news endpoint directly
        """
        date = datetime.fromisoformat(post["date"] + "+00:00")
        return {
            "id": f"{self.name}-{post['id']!s}",
            "title": post["title"]["rendered"],
            "content": clean_html(post["content"]["rendered"]),
            "last_updated": date,
            "display_date": date,
            "channel": None,
            "available_languages": None,
            "source": "tuNews",
            "externalUrl": post["link"],
        }
