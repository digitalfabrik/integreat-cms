"""
This module contains all sitemap classes which are all based on :class:`django.contrib.sitemaps.Sitemap`.
"""
import logging

from abc import ABC, abstractmethod
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap

from ..cms.models import (
    PageTranslation,
    EventTranslation,
    POITranslation,
    OfferTemplate,
)
from ..cms.constants import status

logger = logging.getLogger(__name__)


class WebappSitemap(ABC, Sitemap):
    """
    This is an abstract base class for all webapp sitemaps.
    """

    #: The default change frequency for all sitemap's urls
    changefreq = "monthly"

    #: The default priority for all sitemap's urls
    priority = 0.5

    @property
    @abstractmethod
    def queryset(self):
        """
        Each subclass needs at least a ``queryset`` attribute defined.
        """

    def __init__(self, region, language):
        """
        This init function sets the region and language parameters.

        :param region: The region of this sitemap's urls
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~integreat_cms.cms.models.languages.language.Language
        """
        self.region = region
        self.language = language

    def items(self):
        """
        This functions returns the public translations contained in this sitemap.

        :return: The queryset of translation objects
        :rtype: ~django.db.models.query.QuerySet
        """
        return self.queryset

    @staticmethod
    def lastmod(translation):
        """
        This functions returns the date when a translation was last modified.

        :param translation: The given translation
        :type translation: ~integreat_cms.cms.models.pages.page_translation.PageTranslation,
                           ~integreat_cms.cms.models.events.event_translation.EventTranslation, or
                           ~integreat_cms.cms.models.pois.poi_translation.POITranslation

        :return: The list of urls
        :rtype: ~datetime.datetime
        """
        return translation.last_updated

    def _urls(self, page, protocol, domain):
        """
        This is a patched version of :func:`django.contrib.sitemaps.Sitemap._urls` which adds the alternative languages
        to the list of urls.
        This patch is required because the inbuilt function can only deal with the i18n backend languages and not with
        our custom language model.
        Additionally, it overwrites the protocol and domain of the urls with
        :attr:`~integreat_cms.core.settings.WEBAPP_URL` because out of the box, :doc:`ref/contrib/sitemaps` does only
        support this functionality when used together with :doc:`ref/contrib/sites`.

        :param page: The page for the paginator (will always be ``1`` in our case)
        :type page: int

        :param protocol: The protocol of the urls
        :type protocol: str

        :param domain: The domain of the urls
        :type domain: str

        :return: A list of urls
        :rtype: list [ dict ]
        """
        splitted_url = urlsplit(settings.WEBAPP_URL)
        # Generate list of urls without alternative languages
        urls = super()._urls(page, splitted_url.scheme, splitted_url.hostname)
        for url in urls:
            # Add information about alternative languages
            url["alternates"] = self.sitemap_alternates(url["item"])
        return urls

    # pylint: disable=no-self-use
    def sitemap_alternates(self, obj):
        """
        This function returns the sitemap alternatives for a given object

        :param obj: The object
        :type obj: ~integreat_cms.cms.models.pages.page.Page, ~integreat_cms.cms.models.events.event.Event or ~integreat_cms.cms.models.pois.poi.POI

        :return: The sitemap alternates of the given object
        :rtype: dict
        """
        return obj.sitemap_alternates


class PageSitemap(WebappSitemap):
    """
    This sitemap contains all urls to page translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    """

    #: The priority of this sitemap's urls
    priority = 1.0
    #: The :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` :class:`~django.db.models.query.QuerySet` of this sitemap
    queryset = PageTranslation.objects.filter(status=status.PUBLIC)

    def __init__(self, region, language):
        """
        This init function filters the queryset of page translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~integreat_cms.cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            page__in=self.region.get_pages(return_unrestricted_queryset=True),
            language=self.language,
        )


class EventSitemap(WebappSitemap):
    """
    This sitemap contains all urls to event translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute priority: The priority of this sitemap's urls (see :attr:`WebappSitemap.priority`)
    """

    #: The usual change frequency of this sitemap's urls
    changefreq = "daily"

    #: The :class:`~integreat_cms.cms.models.events.event_translation.EventTranslation` :class:`~django.db.models.query.QuerySet` of this sitemap
    queryset = EventTranslation.objects.filter(
        event__archived=False, status=status.PUBLIC
    )

    def __init__(self, region, language):
        """
        This init function filters the queryset of event translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~integreat_cms.cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            event__in=self.region.events.all(), language=self.language
        )


class POISitemap(WebappSitemap):
    """
    This sitemap contains all urls to POI translations for a specific region and language.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    :attribute priority: The priority of this sitemap's urls (see :attr:`WebappSitemap.priority`)
    """

    #: The :class:`~integreat_cms.cms.models.pois.poi_translation.POITranslation` :class:`~django.db.models.query.QuerySet` queryset of this sitemap
    queryset = POITranslation.objects.filter(poi__archived=False, status=status.PUBLIC)

    def __init__(self, region, language):
        """
        This init function filters the queryset of POI translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~integreat_cms.cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region and language
        self.queryset = self.queryset.filter(
            poi__in=self.region.pois.all(), language=self.language
        )


class OfferSitemap(WebappSitemap):
    """
    This sitemap contains all urls to offers for a specific region.

    Attributes inherited from :class:`~integreat_cms.sitemap.sitemaps.WebappSitemap`:

    :attribute changefreq: The usual change frequency of this sitemap's urls (see :attr:`WebappSitemap.changefreq`)
    """

    #: The priority of this sitemap's urls (``1.0``)
    priority = 1.0
    #: The :class:`~integreat_cms.cms.models.offers.offer_template.OfferTemplate` :class:`~django.db.models.query.QuerySet` queryset of this sitemap
    queryset = OfferTemplate.objects.all()

    def __init__(self, region, language):
        """
        This init function filters the queryset of offers objects based on the given region.

        :param region: The region of this sitemap's urls
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~integreat_cms.cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super().__init__(region, language)
        # Filter queryset based on region
        self.queryset = self.queryset.filter(regions=self.region)

    def location(self, item):
        """
        This location function returns the absolute path for a given object returned by items().

        :param item: Objects passed from items() method
        :type item: ~integreat_cms.cms.models.offers.offer_template.OfferTemplate

        :return: The absolute path of the given offer object
        :rtype: str
        """
        return "/" + "/".join(
            [self.region.slug, self.language.slug, "offers", item.slug]
        )

    def sitemap_alternates(self, obj):
        """
        This sitemap_alternates function returns the language alternatives of offers for the use in sitemaps.

        :param obj: Objects passed from items() method
        :type obj: ~integreat_cms.cms.models.offers.offer_template.OfferTemplate

        :return: A list of dictionaries containing the alternative translations of offers
        :rtype: list [ dict ]
        """
        return [
            {
                "location": f"{settings.WEBAPP_URL}/{self.region.slug}/{language.slug}/offers/{obj.slug}",
                "lang_slug": language.slug,
            }
            for language in self.region.visible_languages
            if language != self.language
        ]
