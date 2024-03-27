"""
This module contains all sitemap classes which are all based on :class:`django.contrib.sitemaps.Sitemap`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap

from ..cms.constants import status
from ..cms.models import (
    EventTranslation,
    OfferTemplate,
    PageTranslation,
    POITranslation,
)

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    from django.db.models.query import QuerySet

    from ..cms.models import Language, Region
    from ..cms.models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


class WebappSitemap(ABC, Sitemap):
    """
    This is an abstract base class for all webapp sitemaps.
    """

    #: The default change frequency for all sitemap's urls
    changefreq: str = "monthly"

    #: The default priority for all sitemap's urls
    priority: float = 0.5

    @property
    @abstractmethod
    def queryset(self) -> QuerySet[OfferTemplate | AbstractContentTranslation]:
        """
        Each subclass needs at least a ``queryset`` attribute defined.
        """

    def __init__(self, region: Region, language: Language) -> None:
        """
        This init function sets the region and language parameters.

        :param region: The region of this sitemap's urls
        :param language: The language of this sitemap's urls
        """
        self.region = region
        self.language = language

    def items(self) -> QuerySet[OfferTemplate | AbstractContentTranslation]:
        """
        This functions returns the public translations contained in this sitemap.

        :return: The queryset of translation objects
        """
        return self.queryset

    @staticmethod
    def lastmod(translation: OfferTemplate | AbstractContentTranslation) -> datetime:
        """
        This functions returns the date when a translation was last modified.

        :param translation: The given translation
                           ~integreat_cms.cms.models.events.event_translation.EventTranslation, or
                           ~integreat_cms.cms.models.pois.poi_translation.POITranslation

        :return: The list of urls
        """
        return translation.last_updated

    def _urls(self, page: int, protocol: str, domain: str) -> list[dict[str, Any]]:
        """
        This is a patched version of :func:`django.contrib.sitemaps.Sitemap._urls` which adds the alternative languages
        to the list of urls.
        This patch is required because the inbuilt function can only deal with the i18n backend languages and not with
        our custom language model.
        Additionally, it overwrites the protocol and domain of the urls with
        :attr:`~integreat_cms.core.settings.WEBAPP_URL` because out of the box, :doc:`django:ref/contrib/sitemaps` does only
        support this functionality when used together with :doc:`django:ref/contrib/sites`.

        :param page: The page for the paginator (will always be ``1`` in our case)
        :param protocol: The protocol of the urls
        :param domain: The domain of the urls
        :return: A list of urls
        """
        splitted_url = urlsplit(settings.WEBAPP_URL)
        # Generate list of urls without alternative languages
        urls = super()._urls(page, splitted_url.scheme, splitted_url.hostname)
        for url in urls:
            # Add information about alternative languages
            url["alternates"] = self.sitemap_alternates(url["item"])
        return urls

    def sitemap_alternates(
        self, obj: OfferTemplate | AbstractContentTranslation
    ) -> list[dict[str, str]]:
        """
        This function returns the sitemap alternatives for a given object

        :param obj: The object
        :return: The sitemap alternates of the given object
        """
        return obj.sitemap_alternates


class PageSitemap(WebappSitemap):
    """
    This sitemap contains all urls to page translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    """

    #: The priority of this sitemap's urls
    priority: float = 1.0
    #: The :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` :class:`~django.db.models.query.QuerySet` of this sitemap
    queryset: QuerySet[PageTranslation] = PageTranslation.objects.filter(
        status=status.PUBLIC
    )

    def __init__(self, region: Region, language: Language) -> None:
        """
        This init function filters the queryset of page translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :param language: The language of this sitemap's urls
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            page__in=self.region.get_pages(),
            language=self.language,
        ).distinct("page__pk")


class EventSitemap(WebappSitemap):
    """
    This sitemap contains all urls to event translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute priority: The priority of this sitemap's urls (see :attr:`WebappSitemap.priority`)
    """

    #: The usual change frequency of this sitemap's urls
    changefreq: str = "daily"

    #: The :class:`~integreat_cms.cms.models.events.event_translation.EventTranslation` :class:`~django.db.models.query.QuerySet` of this sitemap
    queryset: QuerySet[EventTranslation] = EventTranslation.objects.filter(
        event__archived=False, status=status.PUBLIC
    )

    def __init__(self, region: Region, language: Language) -> None:
        """
        This init function filters the queryset of event translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :param language: The language of this sitemap's urls
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            event__in=self.region.events.all(), language=self.language
        ).distinct("event__pk")


class POISitemap(WebappSitemap):
    """
    This sitemap contains all urls to POI translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    :attribute priority: The priority of this sitemap's urls (see :attr:`WebappSitemap.priority`)
    """

    #: The :class:`~integreat_cms.cms.models.pois.poi_translation.POITranslation` :class:`~django.db.models.query.QuerySet` queryset of this sitemap
    queryset: QuerySet[POITranslation] = POITranslation.objects.filter(
        poi__archived=False, status=status.PUBLIC
    )

    def __init__(self, region: Region, language: Language) -> None:
        """
        This init function filters the queryset of POI translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :param language: The language of this sitemap's urls
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            poi__in=self.region.pois.all(), language=self.language
        ).distinct("poi__pk")


class OfferSitemap(WebappSitemap):
    """
    This sitemap contains all urls to offers for a specific region.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    """

    #: The priority of this sitemap's urls (``1.0``)
    priority = 1.0
    #: The :class:`~integreat_cms.cms.models.offers.offer_template.OfferTemplate` :class:`~django.db.models.query.QuerySet` queryset of this sitemap
    queryset: QuerySet[OfferTemplate] = OfferTemplate.objects.all()

    def __init__(self, region: Region, language: Language) -> None:
        """
        This init function filters the queryset of offers objects based on the given region.

        :param region: The region of this sitemap's urls
        :param language: The language of this sitemap's urls
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region
        self.queryset = self.queryset.filter(regions=self.region)

    def location(self, item: OfferTemplate) -> str:
        """
        This location function returns the absolute path for a given object returned by items().

        :param item: Objects passed from items() method
        :return: The absolute path of the given offer object
        """
        return f"/{self.region.slug}/{self.language.slug}/offers/{item.slug}"

    def sitemap_alternates(self, obj: OfferTemplate) -> list[dict[str, str]]:
        """
        This sitemap_alternates function returns the language alternatives of offers for the use in sitemaps.

        :param obj: Objects passed from items() method
        :return: A list of dictionaries containing the alternative translations of offers
        """
        return [
            {
                "location": f"{settings.WEBAPP_URL}/{self.region.slug}/{language.slug}/offers/{obj.slug}",
                "lang_slug": language.slug,
            }
            for language in self.region.visible_languages
            if language != self.language
        ]
