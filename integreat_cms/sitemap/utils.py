"""
This module contains utils for the sitemap app.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .sitemaps import EventSitemap, OfferSitemap, PageSitemap, POISitemap

if TYPE_CHECKING:
    from typing import Any

    from integreat_cms.cms.models.languages.language import Language
    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


def get_sitemaps(region: Region, language: Language) -> list[Any]:
    """
    This helper function generates a list of all non-empty sitemaps for a given region and language
    It is used in :class:`~integreat_cms.sitemap.views.SitemapIndexView` and :class:`~integreat_cms.sitemap.views.SitemapView`.

    :param region: The requested region
    :param language: The requested language
    :return: All sitemaps for the given region and language
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
