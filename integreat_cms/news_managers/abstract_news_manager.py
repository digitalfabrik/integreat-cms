from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest, HttpResponse

    from ..cms.models import Language, Region


class NewsItem(TypedDict):
    id: int
    title: str
    message: str
    timestamp: datetime
    last_updated: datetime
    display_date: datetime
    channel: str | None
    available_languages: dict | None
    source: str
    link: str | None


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
        slug: str,
    ) -> HttpResponse:
        """
        Tries rendering the social media headers for a news page in a specified region and language
        To be implemented in the inheriting model
        """
        raise NotImplementedError
