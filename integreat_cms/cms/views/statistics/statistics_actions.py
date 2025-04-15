"""
This module contains view actions related to pages.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ....matomo_api.matomo_api_client import MatomoException
from ...decorators import permission_required
from ...forms import StatisticsFilterForm

if TYPE_CHECKING:
    from django.http import HttpRequest

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

    try:
        result = region.statistics.get_page_accesses(
            start_date=statistics_form.cleaned_data["start_date"],
            end_date=statistics_form.cleaned_data["end_date"],
            period=statistics_form.cleaned_data["period"],
            region=region,
        )
        return JsonResponse(result, safe=False)
    except TimeoutError:
        logger.exception("Timeout during request to Matomo API")
        return JsonResponse(
            {"error": "Timeout during request to Matomo API"}, status=504
        )
    except MatomoException:
        logger.exception("The request to the Matomo API failed.")
        return JsonResponse(
            {"error": "The request to the Matomo API failed."}, status=500
        )
