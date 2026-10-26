"""
This module includes the endpoint to read the condition statistics of a single region.

The metrics are expensive to compute, so this endpoint never computes them on request — it only
returns the values precomputed every night by
:func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions`, together with the
time they were computed. The machine translation budget is read live from the region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from django.http import JsonResponse

from ...cms.models import RegionCondition
from ..decorators import api_token_required, json_response

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ...cms.models import Region


class Statistics(TypedDict):
    """
    The JSON representation of the statistics of a region

    The condition metrics and ``computed_at`` are ``None`` as long as they have not been computed
    for the region yet, e.g. directly after it was created.
    """

    computed_at: str | None
    num_broken_links: int | None
    num_low_hix_pages: int | None
    num_pages: int | None
    num_pages_with_missing_or_outdated_translation: int | None
    num_outdated_pages: int | None
    num_languages_besides_root_language: int | None
    mt_budget: int
    mt_budget_used: int
    mt_budget_remaining: int


def transform_region_statistics(region: Region) -> Statistics:
    """
    Build the JSON representation of the statistics of a region

    :param region: The region whose statistics should be returned
    :return: The statistics of the region
    """
    condition = RegionCondition.objects.filter(region=region).first()
    return {
        "computed_at": condition.computed_at.isoformat() if condition else None,
        "num_broken_links": condition.num_broken_links if condition else None,
        "num_low_hix_pages": condition.num_low_hix_pages if condition else None,
        "num_pages": condition.num_pages if condition else None,
        "num_pages_with_missing_or_outdated_translation": (
            condition.num_pages_with_missing_or_outdated_translation
            if condition
            else None
        ),
        "num_outdated_pages": condition.num_outdated_pages if condition else None,
        "num_languages_besides_root_language": (
            condition.num_languages_besides_root_language if condition else None
        ),
        "mt_budget": region.mt_budget,
        "mt_budget_used": region.mt_budget_used,
        "mt_budget_remaining": region.mt_budget_remaining,
    }


@json_response
@api_token_required("cms.view_region")
def region_statistics(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Return the precomputed condition statistics of a region

    :param request: Django request
    :param region_slug: The slug of the region
    :return: The statistics of the region
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request."}, status=405)
    return JsonResponse(transform_region_statistics(request.region))
