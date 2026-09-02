from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

from django.conf import settings
from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import render
from lxml import etree
from lxml.html import fromstring

from ..cms.models import Region
from ..cms.utils.content_utils import sanitize_html, sanitize_html_element
from ..cms.utils.social_media_utils import render_social_media_headers

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest, HttpResponse

    from ..cms.models import Language

logger = logging.getLogger(__name__)

_CACHE_MISS = object()


class NewsItem(TypedDict):
    id: str
    title: str
    content: str
    last_updated: datetime
    published_at: datetime
    display_date: datetime
    channel: str | None
    available_languages: dict | None
    source: str
    externalUrl: str


def clean_html(html_string: str) -> str:
    """
    Remove unnecessary HTML elements from a Tü News post body.
    """
    main = fromstring("<main>" + html_string + "</main>")
    xpath_pvc = '//*[contains(@class, "pvc_")]'

    for pvc in main.xpath(xpath_pvc):
        pvc.getparent().remove(pvc)

    # External news are not created in our own editor, so they are not sanitized on save
    sanitize_html_element(main)

    return etree.tostring(main, pretty_print=True).decode("utf-8")


class AbstractNewsManager(ABC):
    short_name: str
    name: str

    @abstractmethod
    def import_news_items(self) -> None:
        """
        Imports news items from the source

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    def get_cached_news_items(self, language_slug: str) -> list[NewsItem]:
        """
        Return the cached news items for the given language.

        If the cache key does not exist yet (i.e. the cache has not been warmed
        up), the news items are imported from the source on demand and the cache
        is populated before returning.
        """
        cache_key = f"{self.short_name}:{language_slug}"
        posts = cache.get(cache_key, _CACHE_MISS)
        if posts is _CACHE_MISS:
            if not settings.EXTERNALNEWS_DISABLE_AUTO_REIMPORT:
                logger.info(
                    "Cache miss for %s; importing news items on demand.", cache_key
                )
                self.import_news_items()
                posts = cache.get(cache_key, [])
            else:
                return []
        return posts

    def collect_news_items(
        self, region_slug: str, language_slug: str, _channel: str
    ) -> list[NewsItem]:
        """
        Returns news items imported from the source
        """
        try:
            if not Region.objects.get(slug=region_slug).external_news_enabled:
                logger.error("External news not enabled: %s", region_slug)
                return []
        except Region.DoesNotExist:
            logger.exception("Region not found: %s", region_slug)
            return []
        return self.get_cached_news_items(language_slug)

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

    def raw_content(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_raw_id: str,
    ) -> HttpResponse:
        """
        Tries rendering the raw HTML content for a news page in a specified region and language
        """
        post = self.find_post(region, language, news_raw_id)

        return render(
            request,
            "raw_content.html",
            {
                "title": post["title"],
                # Posts which were cached before they were sanitized on import are not necessarily safe
                "content": sanitize_html(post["content"]),
                "language_code": language.bcp47_tag,
            },
        )

    def get_single_news(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_id: str,
    ) -> JsonResponse:
        """
        Returns a news item that is imported from the source and matches the id
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
        posts = self.get_cached_news_items(language.slug)
        post = next(
            (
                post
                for post in posts
                if post["id"] == f"{self.short_name}-{news_raw_id}"
            ),
            None,
        )

        if not post:
            raise Http404(
                f"{self.name} post not found in this region with this news ID."
            )
        return post
