"""
This module contains view actions related to pages.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import date, timedelta
from typing import TYPE_CHECKING

from celery import shared_task
from django.db.models import OuterRef
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.models.regions.region import Region

from ....matomo_api.matomo_api_client import MatomoException
from ...decorators import permission_required
from ...forms import StatisticsFilterForm

if TYPE_CHECKING:
    from django.http import HttpRequest


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
TIME_TO_NEXT_FETCH_ATTEMPT = 120


@permission_required("cms.view_statistics")
def get_total_visits_ajax(
    request: HttpRequest,
    region_slug: str,  # pylint: disable=unused-argument
) -> JsonResponse:
    """
    Aggregates the total API hits of the last 14 days and renders a Widget for the Dashboard.

    :param request: The current request
    :return: A JSON with all API-Hits of the last 2 weeks
    """

    region = request.region

    if not region.statistics_enabled:
        logger.error("Statistics are not enabled for this region.")
        return JsonResponse(
            {"error": "Statistics are not enabled for this region."},
            status=500,
        )

    start_date = date.today() - timedelta(days=15)
    end_date = date.today() - timedelta(days=1)

    try:
        result = region.statistics.get_total_visits(
            start_date=start_date,
            end_date=end_date,
        )
        return JsonResponse(result)
    except TimeoutError:
        logger.exception("Timeout during request to Matomo API")
        return JsonResponse(
            {"error": "Timeout during request to Matomo API"},
            status=504,
        )
    except MatomoException:
        logger.exception("The request to the Matomo API failed.")
        return JsonResponse(
            {"error": "The request to the Matomo API failed."},
            status=500,
        )


@require_POST
def get_visits_per_language_ajax(
    request: HttpRequest,
    region_slug: str,  # pylint: disable=unused-argument
) -> JsonResponse:
    """
    Ajax method to request the app hits for a certain timerange distinguished by languages.

    :param request: The current request
    :return: A JSON with all API-Hits of the requested time period
    """

    region = request.region

    if not region.statistics_enabled:
        logger.error("Statistics are not enabled for this region.")
        return JsonResponse(
            {"error": "Statistics are not enabled for this region."},
            status=500,
        )

    statistics_form = StatisticsFilterForm(data=request.POST)

    if not statistics_form.is_valid():
        logger.error(statistics_form.errors)
        return JsonResponse(
            {"errors": statistics_form.errors},
            status=400,
        )

    try:
        result = region.statistics.get_visits_per_language(
            start_date=statistics_form.cleaned_data["start_date"],
            end_date=statistics_form.cleaned_data["end_date"],
            period=statistics_form.cleaned_data["period"],
        )
        return JsonResponse(result, safe=False)
    except TimeoutError:
        logger.exception("Timeout during request to Matomo API")
        return JsonResponse(
            {"error": "Timeout during request to Matomo API"},
            status=504,
        )
    except MatomoException:
        logger.exception("The request to the Matomo API failed.")
        return JsonResponse(
            {"error": "The request to the Matomo API failed."},
            status=500,
        )


@require_POST
# pylint: disable=unused-argument
def get_page_accesses_ajax(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Ajax method to request the accesses per page for a certain timerange distinguished by languages.

    :param request: The current request
    :param region_slug: The slug of the current region
    :return: A JSON with all API-Hits of the requested time period
    """
    region = request.region

    if not region.statistics_enabled:
        logger.error("Statistics are not enabled for this region.")
        return JsonResponse(
            {"error": "Statistics are not enabled for this region."}, status=500
        )

    statistics_form = StatisticsFilterForm(data=request.POST)

    if not statistics_form.is_valid():
        logger.error(statistics_form.errors)
        return JsonResponse(
            {"errors": statistics_form.errors},
            status=400,
        )

    region_pages = Page.objects.filter(region=region)
    languages = region.languages
    page_access_sums = region.get_page_access_count_by_language(
        pages=region_pages,
        start_date=statistics_form.cleaned_data["start_date"],
        end_date=statistics_form.cleaned_data["end_date"],
        languages=languages,
    )

    page_accesses_dict: dict[str, dict[str, int]] = defaultdict(dict)
    for access_sum in page_access_sums:
        page_id = str(access_sum["page__id"])
        language_slug = str(access_sum["language__slug"])
        page_accesses_dict[page_id][language_slug] = access_sum["total_accesses"]

    return JsonResponse(page_accesses_dict, safe=False)


def fetch_page_accesses(
    start_date: date, end_date: date, region: Region, times_tried: int = 0
) -> None:
    """
    Load page accesses synchronuos from Matomo and save them to page accesses model
    :param start_date: Earliest date
    :param end_date: Latest date
    :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
    :param region: The region for which we want our page based accesses
    """
    logger.info("Start fetching page accesses from Matomo for %s", region)
    languages = list(region.active_languages)
    pages = region.get_pages()
    region_slug = region.slug
    times_tried = times_tried + 1

    # Query PageTranslation and the related Page and Language objects directly from the database to avoid calling data from the cache, due to celery starting with an empty cache
    subquery = (
        PageTranslation.objects.filter(
            page_id=OuterRef("page_id"), language=OuterRef("language")
        )
        .order_by("-version")
        .values("pk")[:1]
    )
    prefetched_translations = PageTranslation.objects.filter(
        page__in=pages, pk__in=subquery
    ).select_related("page", "language")

    try:
        region.statistics.get_page_accesses(
            start_date=start_date,
            end_date=end_date,
            region_slug=region_slug,
            languages=languages,
            pages=pages,
            prefetched_translations=prefetched_translations,
        )
    except MatomoException:
        if times_tried < MAX_ATTEMPTS:
            logger.exception(
                "Matomo not reachable, trying again in 2 Minutes for %s", region
            )
            time.sleep(TIME_TO_NEXT_FETCH_ATTEMPT)
            fetch_page_accesses(
                start_date=start_date,
                end_date=end_date,
                region=region,
                times_tried=times_tried,
            )
        else:
            logger.exception(
                "Matomo remains not reachable for %s. Skipping region", region
            )


@shared_task
def async_fetch_page_accesses(start_date: date, end_date: date, region_id: int) -> None:
    """
    Fetch page accesses async with celery from Matomo and save them to page accesses model

    :param start_date: Earliest date
    :param end_date: Latest date
    :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
    :param region: The region for which we want our page based accesses
    """
    region = Region.objects.get(id=region_id)
    fetch_page_accesses(
        start_date=start_date,
        end_date=end_date,
        region=region,
    )
