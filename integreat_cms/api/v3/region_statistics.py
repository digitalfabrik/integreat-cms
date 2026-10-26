"""
This module includes the endpoint to read the condition statistics of a single region.

The condition metrics are expensive to compute, so this endpoint never computes them on request.
It only returns the values precomputed every night by
:func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions`, together with the
time they were computed. ``computed_at`` tells how old they are: they can be older than a day if the
last runs failed for the region. The machine translation budget is read live from the region.
"""

from __future__ import annotations

from typing import cast, TYPE_CHECKING, TypedDict

from django.http import JsonResponse

from ...cms.models import RegionCondition
from ..decorators import api_token_required, json_response

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ...cms.models import Region


class Condition(TypedDict):
    """
    The stored condition metrics of a region

    The metrics mirror :attr:`~integreat_cms.cms.models.regions.region_condition.RegionCondition.METRICS`
    — this is asserted in ``tests.api.test_region_statistics`` — and ``num_low_hix_pages`` counts
    page translations, not pages.
    """

    computed_at: str
    num_broken_links: int
    num_low_hix_pages: int
    num_pages: int
    num_pages_with_missing_or_outdated_translation: int
    num_outdated_pages: int
    num_languages_besides_root_language: int


class Statistics(TypedDict):
    """
    The JSON representation of the statistics of a region

    ``condition`` is ``None`` as long as no run has stored a condition for the region yet, e.g. for
    a new region or one whose computation has always failed. Otherwise all of its metrics are set.
    The budget values are always current.
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
    # Read dynamically to keep the model the single source of truth for the metric names, which
    # the type checker cannot verify against the keys of the typed dictionary
    return cast(
        "Condition",
        {
            "computed_at": condition.computed_at.isoformat(),
            **{
                metric: getattr(condition, metric) for metric in RegionCondition.METRICS
            },
        },
    )


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
