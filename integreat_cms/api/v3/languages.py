"""
This module includes functions related to the languages API endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404, JsonResponse

from ...cms.constants import region_status
from ..decorators import json_response

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models.languages.language import Language


def transform_language(language: Language) -> dict[str, Any]:
    """
    Function to create a JSON from a single language object.

    :param language: The language object which should be converted
    :return: data necessary for API
    """
    return {
        "id": language.id,
        "code": language.slug,
        "bcp47_tag": language.bcp47_tag,
        "native_name": language.native_name,
        "dir": language.text_direction,
    }


@json_response
# pylint: disable=unused-argument
def languages(request: HttpRequest, region_slug: str) -> JsonResponse:
    """
    Function to add all languages related to a region to a JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :return: JSON object according to APIv3 languages endpoint definition
    """
    if request.region.status == region_status.ARCHIVED:
        raise Http404("This region is archived.")

    return JsonResponse(
        list(map(transform_language, request.region.visible_languages)), safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
