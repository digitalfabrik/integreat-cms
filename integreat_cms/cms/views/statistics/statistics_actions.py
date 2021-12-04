"""
This module contains view actions related to pages.
"""
import logging

from datetime import date, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ...forms import StatisticsFilterForm
from ...utils.matomo_api_manager import MatomoException

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
def get_total_visits_ajax(request, region_slug):
    """
    Aggregates the total API hits of the last 14 days and renders a Widget for the Dashboard.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A JSON with all API-Hits of the last 2 weeks
    :rtype: ~django.http.JsonResponse
    """

    region = request.region

    if not region.statistics_enabled:
        return JsonResponse(
            {"error": "Statistics are not enabled for this region."}, status=500
        )

    start_date = date.today() - timedelta(days=15)
    end_date = date.today() - timedelta(days=1)

    try:
        result = region.statistics.get_total_visits(
            start_date=start_date, end_date=end_date
        )
        return JsonResponse(result)
    except MatomoException as e:
        logger.exception(e)
        return JsonResponse(
            {"error": "The request to the Matomo API failed."}, status=500
        )


@require_POST
# pylint: disable=unused-argument
def get_visits_per_language_ajax(request, region_slug):
    """
    Ajax method to request the app hits for a certain timerange distinguished by languages.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A JSON with all API-Hits of the requested time period
    :rtype: ~django.http.JsonResponse
    """

    region = request.region

    if not region.statistics_enabled:
        return JsonResponse(
            {"error": "Statistics are not enabled for this region."}, status=500
        )

    statistics_form = StatisticsFilterForm(data=request.POST)

    if not statistics_form.is_valid():
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
    except MatomoException as e:
        logger.exception(e)
        return JsonResponse(
            {"error": "The request to the Matomo API failed."}, status=500
        )
