"""
This module includes the endpoint to read the statistics of a single region.

The condition metrics are not computed on request, but precomputed every night by
:func:`~integreat_cms.cms.utils.region_condition_utils.update_region_conditions`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from django.http import JsonResponse

from ...cms.models import RegionCondition
from ...cms.utils.region_condition_utils import COMPUTED_STATUSES
from ..decorators import api_token_required, json_response

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ...cms.models import Region


class Condition(TypedDict):
    """
    The stored condition metrics of a region

    The keys are listed explicitly, so renaming a model field cannot silently change the API.
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

    ``condition`` is ``None`` if the region has not been computed yet or is no longer active or
    hidden.
    """

    condition: Condition | None
    mt_budget: int
    mt_budget_used: int
    mt_budget_remaining: int


def _transform_region_condition(condition: RegionCondition) -> Condition:
    """
    Build the JSON representation of a stored region condition

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


def _transform_region_statistics(
    region: Region,
    condition: RegionCondition | None,
) -> Statistics:
    """
    Build the JSON representation of the statistics of a region

    :param region: The region
    :param condition: The newest stored condition of the region, if any
    :return: The statistics of the region
    """
    return {
        "condition": _transform_region_condition(condition) if condition else None,
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
    region = request.region
    # The history of an archived region is kept, but it has no current condition
    condition = (
        RegionCondition.objects.filter(
            region=region,
            region__status__in=COMPUTED_STATUSES,
        )
        .order_by("-computed_at")
        .first()
    )
    return JsonResponse(_transform_region_statistics(region, condition))
