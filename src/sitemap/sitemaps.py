"""
This module contains all sitemap classes which are all based on :class:`django.contrib.sitemaps.Sitemap`.
"""
from abc import ABC, abstractmethod
from urllib.parse import urlsplit

from django.contrib.sitemaps import Sitemap

from backend.settings import WEBAPP_URL
from cms.models import PageTranslation, EventTranslation, POITranslation
from cms.constants import status


class WebappSitemap(ABC, Sitemap):
    """
    This is an abstract base class for all webapp sitemaps.

    :param changefreq: The default change frequency for all sitemap's urls (``monthly``)
    :type changefreq: str

    :param priority: The default priority for all sitemap's urls (``0.5``)
    :type priority: float

    .. automethod:: _urls
    """

    changefreq = "monthly"
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
        :type region: ~cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~cms.models.languages.language.Language
        """
        self.region = region
        self.language = language

    def items(self):
        """
        This functions returns the public translations contained in this sitemap.

        :return: The queryset of translation objects
        :rtype: :class:`~django.db.models.query.QuerySet`
        """
        return self.queryset

    @staticmethod
    def lastmod(translation):
        """
        This functions returns the date when a translation was last modified.

        :param translation: The given translation
        :type translation: :class:`~cms.models.pages.page_translation.PageTranslation`,
                           :class:`~cms.models.events.event_translation.EventTranslation` or
                           :class:`~cms.models.pois.poi_translation.POITranslation`

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
        Additionally, it overwrites the protocol and domain of the urls with :setting:`WEBAPP_URL` because out of the
        box, :doc:`ref/contrib/sitemaps` does only support this functionality when used together with
        :doc:`ref/contrib/sites`.

        :param page: The page for the paginator (will always be ``1`` in our case)
        :type page: int

        :param protocol: The protocol of the urls
        :type protocol: str

        :param domain: The domain of the urls
        :type domain: str

        :return: A list of urls
        :rtype: list [ dict ]
        """
        splitted_url = urlsplit(WEBAPP_URL)
        # Gemerate list of urls without alternative languages
        urls = super(WebappSitemap, self)._urls(
            page, splitted_url.scheme, splitted_url.hostname
        )
        for url in urls:
            # Add information about alternative languages
            url["alternates"] = url["item"].sitemap_alternates
        return urls


class PageSitemap(WebappSitemap):
    """
    This sitemap contains all urls to page translations for a specific region and language.

    :param priority: The priority of this sitemap's urls (``1.0``)
    :type priority: float

    :param queryset: The queryset of this sitemap
    :type queryset: :class:`~django.db.models.query.QuerySet` [ :class:`~cms.models.pages.page_translation.PageTranslation` ]

    Parameters inherited from :class:`~sitemap.sitemaps.WebappSitemap`:

    :param changefreq: The usual change frequency of this sitemap's urls (``monthly``)
    :type changefreq: str
    """

    priority = 1.0
    queryset = PageTranslation.objects.filter(
        page__archived=False, status=status.PUBLIC
    )

    def __init__(self, region, language):
        """
        This init function filters the queryset of page translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super(PageSitemap, self).__init__(region, language)
        # Filter queryset based on region and langauge
        self.queryset = self.queryset.filter(
            page__in=self.region.pages.all(), language=self.language
        )


class EventSitemap(WebappSitemap):
    """
    This sitemap contains all urls to event translations for a specific region and language.

    :param changefreq: The usual change frequency of this sitemap's urls (``daily``)
    :type changefreq: str

    :param queryset: The queryset of this sitemap
    :type queryset: :class:`~django.db.models.query.QuerySet` [ :class:`~cms.models.events.event_translation.EventTranslation` ]

    Parameters inherited from :class:`~sitemap.sitemaps.WebappSitemap`:

    :param priority: The priority of this sitemap's urls (``0.5``)
    :type priority: float
    """

    changefreq = "daily"
    queryset = EventTranslation.objects.filter(
        event__archived=False, status=status.PUBLIC
    )

    def __init__(self, region, language):
        """
        This init function filters the queryset of event translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super(EventSitemap, self).__init__(region, language)
        # Filter queryset based on region and langauge
        self.queryset = self.queryset.filter(
            event__in=self.region.events.all(), language=self.language
        )


class POISitemap(WebappSitemap):
    """
    This sitemap contains all urls to POI translations for a specific region and language.

    :param queryset: The queryset of this sitemap
    :type queryset: :class:`~django.db.models.query.QuerySet` [ :class:`~cms.models.pois.poi_translation.POITranslation` ]

    Parameters inherited from :class:`~sitemap.sitemaps.WebappSitemap`:

    :param changefreq: The usual change frequency of this sitemap's urls (``monthly``)
    :type changefreq: str

    :param priority: The priority of this sitemap's urls (``0.5``)
    :type priority: float
    """

    queryset = POITranslation.objects.filter(poi__archived=False, status=status.PUBLIC)

    def __init__(self, region, language):
        """
        This init function filters the queryset of POI translation objects based on the given region and language.

        :param region: The region of this sitemap's urls
        :type region: ~cms.models.regions.region.Region

        :param language: The language of this sitemap's urls
        :type language: ~cms.models.languages.language.Language
        """
        # Instantiate WebappSitemap
        super(POISitemap, self).__init__(region, language)
        # Filter queryset based on region and langauge
        self.queryset = self.queryset.filter(
            poi__in=self.region.pois.all(), language=self.language
        )
