from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest, HttpResponse, JsonResponse

    from ..cms.models import Language, Region


class NewsItem(TypedDict):
    id: str
    title: str
    content: str
    last_updated: datetime
    display_date: datetime
    channel: str | None
    available_languages: dict | None
    source: str
    externalUrl: str


class AbstractNewsManager(ABC):
    name: str

    @abstractmethod
    def import_news_items(self) -> None:
        """
        Imports news items from the source

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @abstractmethod
    def collect_news_items(
        self, region_slug: str, language_slug: str, channel: str
    ) -> list[NewsItem]:
        """
        Returns news items imported from the source

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @abstractmethod
    def social_media_headers(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_raw_id: str,
    ) -> HttpResponse:
        """
        Tries rendering the social media headers for a news page in a specified region and language
        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
