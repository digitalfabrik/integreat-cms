"""
This module includes the endpoint to read the condition statistics of a single region.

The condition metrics are expensive to compute, so this endpoint never computes them on request.
It only returns the values precomputed every night by
:func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions`, together with the
time they were computed. ``computed_at`` tells how old they are: they can be older than a day if the
last runs failed for the region, did not reach it in time, or did not run at all. The machine
translation budget is read live from the region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from django.http import JsonResponse

from ...cms.models import RegionCondition
from ..decorators import api_token_required, json_response

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ...cms.models import Region


class Condition(TypedDict):
    """
    The stored condition metrics of a region

    The keys are the public names of the metrics. They are listed explicitly instead of being
    derived from :attr:`~integreat_cms.cms.models.regions.region_condition.RegionCondition.METRICS`,
    so renaming a model field cannot silently rename a key of the API;
    ``test_metrics_match_the_model_and_the_api`` makes sure every metric is exposed.
    """

    computed_at: str
    num_broken_links: int
    num_low_hix_page_translations: int
    num_pages: int
    num_pages_with_missing_or_outdated_translation: int
    num_outdated_pages: int
    num_languages_besides_root_language: int


class Statistics(TypedDict):
    """
    The JSON representation of the statistics of a region

    ``condition`` is ``None`` if no condition is stored for the region: it has not been computed
    yet (a new region, or one whose computation has always failed), or the region is no longer
    active or hidden. Otherwise all of its metrics are set. The budget values are always current.
    """

    condition: Condition | None
    mt_budget: int
    mt_budget_used: int
    mt_budget_remaining: int


def transform_region_condition(condition: RegionCondition) -> Condition:
    """
    Build the JSON representation of the stored condition of a region

    :param condition: The stored condition
    :return: The condition metrics with the time they were computed
    """
    return {
        "computed_at": condition.computed_at.isoformat(),
        "num_broken_links": condition.num_broken_links,
        "num_low_hix_page_translations": condition.num_low_hix_pages,
        "num_pages": condition.num_pages,
        "num_pages_with_missing_or_outdated_translation": (
            condition.num_pages_with_missing_or_outdated_translation
        ),
        "num_outdated_pages": condition.num_outdated_pages,
        "num_languages_besides_root_language": (
            condition.num_languages_besides_root_language
        ),
    }


def transform_region_statistics(region: Region) -> Statistics:
    """
    Build the JSON representation of the statistics of a region

    :param region: The region whose statistics should be returned
    :return: The statistics of the region
    """
    condition = RegionCondition.objects.filter(region=region).first()
    return {
        "condition": transform_region_condition(condition) if condition else None,
        "mt_budget": region.mt_budget,
        "mt_budget_used": region.mt_budget_used,
        "mt_budget_remaining": region.mt_budget_remaining,
    }


@json_response
@api_token_required("cms.view_region")
def region_statistics(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Return the stored condition metrics of a region and its current machine translation budget

    The region membership of the token's user is not checked: ``cms.view_region`` is only held by
    staff roles, which may see all regions anyway.

    :param request: Django request
    :param region_slug: The slug of the region
    :return: The statistics of the region
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request."}, status=405)
    return JsonResponse(transform_region_statistics(request.region))
