"""
This module includes the endpoint to read and write the settings of a single region.

The endpoint is generic on purpose — it is not scoped to a specific consumer — but it only exposes
the settings which an external system is allowed to manage
(see :mod:`~integreat_cms.cms.constants.region_api_settings`). Core fields such as the name or the
slug identify the region and are deliberately not writable.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone

from ...cms.constants import region_api_settings
from ..decorators import api_token_required, json_response

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models import Region

logger = logging.getLogger(__name__)


def transform_region_settings(region: Region) -> dict[str, Any]:
    """
    Build the JSON representation of the writable settings of a region

    The read side intentionally mirrors the writable fields, so a consumer can fetch the current
    state, change a value and send the same structure back.

    :param region: The region whose settings should be returned
    :return: The settings of the region
    """
    settings = {
        field: getattr(region, field) for field in region_api_settings.WRITABLE_FIELDS
    }
    # Derived values which are useful for the consumer but not writable
    settings["mt_budget"] = region.mt_budget
    settings["mt_budget_used"] = region.mt_budget_used
    settings["mt_budget_remaining"] = region.mt_budget_remaining
    settings["api_settings_synced_at"] = (
        region.api_settings_synced_at.isoformat()
        if region.api_settings_synced_at
        else None
    )
    return settings


@json_response
@api_token_required("cms.change_region")
def region_settings(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Read or write the settings of a region

    ``GET`` returns the current settings, ``POST`` updates the supplied subset of the writable
    fields and records the sync timestamp.

    :param request: Django request
    :param region_slug: The slug of the region
    :return: The settings of the region
    """
    region = request.region

    if request.method == "GET":
        return JsonResponse(transform_region_settings(region))

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request."}, status=405)

    try:
        data = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Expected a JSON object."}, status=400)

    if unknown_fields := sorted(set(data) - set(region_api_settings.WRITABLE_FIELDS)):
        return JsonResponse(
            {
                "error": f"Unknown or read-only fields: {', '.join(unknown_fields)}",
            },
            status=400,
        )

    for field, value in data.items():
        setattr(region, field, value)

    # Enforce the model level validation, e.g. that the budget values are integers and that the
    # renewal month is one of the valid choices. Only the submitted fields are validated, so a
    # request is not rejected because of pre-existing invalid data in an unrelated field.
    untouched_fields = [
        field.name for field in region._meta.fields if field.name not in data
    ]
    try:
        region.full_clean(exclude=untouched_fields, validate_unique=False)
    except ValidationError as e:
        return JsonResponse({"error": e.message_dict}, status=400)

    region.api_settings_synced_at = timezone.now()
    region.save(
        update_fields=[*data.keys(), "api_settings_synced_at"],
    )
    logger.info(
        "Settings of %r updated via API by %r (fields: %s)",
        region,
        request.user,
        ", ".join(sorted(data)),
    )
    return JsonResponse(transform_region_settings(region))
