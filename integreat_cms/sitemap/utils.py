"""
This module contains utils for the sitemap app.
"""
import logging

from .sitemaps import PageSitemap, EventSitemap, POISitemap, OfferSitemap


logger = logging.getLogger(__name__)


def get_sitemaps(region, language):
    """
    This helper function generates a list of all non-empty sitemaps for a given region and language
    It is used in :class:`~integreat_cms.sitemap.views.SitemapIndexView` and :class:`~integreat_cms.sitemap.views.SitemapView`.

    :param region: The requested region
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param language: The requested language
    :type language: ~integreat_cms.cms.models.languages.language.Language


    :return: All sitemaps for the given region and language
    :rtype: list [ ~sitemap.sitemaps.WebappSitemap ]
    """
    sitemaps = [
        PageSitemap(region, language),
        POISitemap(region, language),
        OfferSitemap(region, language),
    ]
    if region.events_enabled:
        sitemaps.append(EventSitemap(region, language))

    # Only return sitemaps which actually contain items
    sitemaps = [sitemap for sitemap in sitemaps if sitemap.items().exists()]

    logger.debug("Sitemaps for %r and %r: %r", region, language, sitemaps)

    return sitemaps
