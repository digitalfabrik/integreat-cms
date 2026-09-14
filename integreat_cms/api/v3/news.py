"""
This module contains API views for news endpoints — the per-source push-notification
feed and the combined feed across all news sources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.paginator import Paginator
from django.http import Http404, JsonResponse

from integreat_cms.cms.views.mixins import get_safe_page

from ...news_managers import registry
from ..decorators import json_response

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@json_response
def sent_push_notifications(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Function to iterate through all sent push notifications related to a region and adds them to a JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON object according to APIv3 push notifications definition
    """
    channel = request.GET.get("channel", "all")
    result = registry.PUSHNEWS.collect_news_items_for_fcm(
        region_slug, language_slug, channel
    )
    return JsonResponse(result, safe=False)


@json_response
def news(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Function to iterate through all available news sources for a region and collect their
    items into one JSON list, sorted by display date (most recent first).

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON list of news items merged across all sources defined in :data:`~integreat_cms.news_managers.registry.CHOICES`
    """
    channel = request.GET.get("channel", "all")

    result = []
    logger.debug(registry.CHOICES)
    for news_manager in registry.CHOICES:
        result.extend(
            news_manager.collect_news_items(region_slug, language_slug, channel)
        )

    sorted_result = sorted(result, key=lambda i: i["display_date"], reverse=True)

    sources = request.GET.getlist("source")
    if sources:
        sorted_result = [
            result for result in sorted_result if result["source"] in sources
        ]

    try:
        page_size = min(int(request.GET.get("size", 20)), 500)
    except (TypeError, ValueError):
        page_size = 20

    if "page" not in request.GET and "size" not in request.GET:
        return JsonResponse(list(sorted_result), safe=False)
    page_num = request.GET.get("page", 1)
    paginator = Paginator(sorted_result, page_size)
    page = get_safe_page(paginator, page_num)

    return JsonResponse(list(page.object_list), safe=False)


@json_response
def single_news(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    news_id: str,
) -> JsonResponse:
    """
    Function to collect and return an news item which matched the given news id.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :param news_id: id of the requested news item
    :return: JSON single NewsItem
    """
    region = request.region
    language = region.get_language_or_404(language_slug, only_active=True)

    parts = news_id.rsplit("-", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        raise Http404("Invalid news id.")
    news_type, raw_id = parts

    news_manager = next(
        (
            news_manager
            for news_manager in registry.CHOICES
            if news_manager.short_name == news_type
        ),
        None,
    )

    if not news_manager:
        raise Http404("No matching news source was found.")

    return news_manager.get_single_news(request, region, language, raw_id)
