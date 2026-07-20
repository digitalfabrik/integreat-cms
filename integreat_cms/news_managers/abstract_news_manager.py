from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import StringIO
from typing import TYPE_CHECKING, TypedDict

from django.core.cache import cache
from django.http import Http404, JsonResponse
from lxml import etree

from ..cms.models import Region
from ..cms.utils.social_media_utils import render_social_media_headers

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest, HttpResponse

    from ..cms.models import Language

logger = logging.getLogger(__name__)


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
    root = etree.parse(  # noqa: S320
        StringIO("<main>" + html_string + "</main>"), etree.HTMLParser()
    )
    xpath_pvc = '//*[contains(@class, "pvc_")]'

    for pvc in root.xpath(xpath_pvc):
        pvc.getparent().remove(pvc)
    main = root.xpath("body/main")[0]

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

    def collect_news_items(
        self, region_slug: str, language_slug: str, _channel: str
    ) -> list[NewsItem]:
        """
        Returns news items imported from the source
        """
        posts = cache.get(f"{self.short_name}:{language_slug}", [])
        if not posts:
            return []
        try:
            if not Region.objects.get(slug=region_slug).external_news_enabled:
                logger.exception("External news not enabled: %s", region_slug)
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
        posts = cache.get(f"{self.short_name}:{language.slug}", [])
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
