"""
This module contains view actions related to pages.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, TYPE_CHECKING

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from integreat_cms.cms.models.languages.language import Language
from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.statistics.page_accesses import PageAccesses

from ....matomo_api.matomo_api_client import MatomoException
from ...decorators import permission_required
from ...forms import StatisticsFilterForm

if TYPE_CHECKING:
    from django.http import HttpRequest

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


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
    Ajax method to request the app hits for a certain timerange distinguished by languages.

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
    page_accesses = region.get_page_accesses_by_language(
        pages=region_pages,
        start_date=statistics_form.cleaned_data["start_date"],
        end_date=statistics_form.cleaned_data["end_date"],
        languages=languages,
    )

    language_slug_table = Language.objects.only("id", "slug")

    page_accesses_dict: dict[Any, Any] = {}
    for access in page_accesses:
        page_id = str(access["page_id"])
        language_slug = language_slug_table.filter(id=access["language_id"]).values(
            "slug"
        )[0]["slug"]
        if page_id in page_accesses_dict:
            if language_slug in page_accesses_dict[page_id]:
                page_accesses_dict[page_id][language_slug][
                    access["access_date"].strftime("%Y-%m-%d")
                ] = access["accesses"]
            else:
                page_accesses_dict[page_id][language_slug] = {
                    access["access_date"].strftime("%Y-%m-%d"): access["accesses"]
                }
        else:
            page_accesses_dict[page_id] = {
                language_slug: {
                    access["access_date"].strftime("%Y-%m-%d"): access["accesses"]
                }
            }

    return JsonResponse(page_accesses_dict, safe=False)


def fetch_page_accesses(
    start_date: date, end_date: date, period: str, region: Region
) -> None:
    """
    Load page accesses from Matomo and save them to page accesses model

    :param start_date: Earliest date
    :param end_date: Latest date
    :param period: The period (one of :attr:`~integreat_cms.cms.constants.matomo_periods.CHOICES`)
    :param region: The region for which we want our page based accesses
    """
    result = region.statistics.get_page_accesses(
        start_date=start_date,
        end_date=end_date,
        period=period,
        region=region,
    )

    accesses = [
        PageAccesses(
            access_date=access_date,
            language=Language.objects.get(slug=language),
            page=Page.objects.get(id=page),
            accesses=result[page][language][access_date],
        )
        for page in result
        for language in result[page]
        for access_date in result[page][language]
    ]
    PageAccesses.objects.bulk_create(
        accesses,
        update_conflicts=True,
        unique_fields=["page", "language", "access_date"],
        update_fields=["accesses"],
    )
