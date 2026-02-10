from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ...search.suggest import suggest_tokens_for_model
from .utils import get_model_cls_from_object_type, REGION_FILTER_FIELDS

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)

#: The maximum number of suggestions returned by :func:`search_suggest`
MAX_RESULT_COUNT: int = 20


@require_POST
def search_suggest(
    request: HttpRequest,
    region_slug: str | None = None,
    language_slug: str | None = None,
) -> JsonResponse:
    """
    Provides a list of search term suggestions based on a search query.
    Uses trigram similarity to find and score matching tokens from model fields.

    :param request: The current request
    :param region_slug: The slug of the current region (optional)
    :param language_slug: The slug of the current language (optional)
    :raises ~django.core.exceptions.PermissionDenied: If the user has no permission to view the object type
    :raises AttributeError: If the request contains an unknown object type or missing required parameters
    :return: JSON response containing ranked search suggestions
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    query: str = body.get("query_string", "")
    object_type: str | None = body.get("object_type")

    if not object_type:
        return JsonResponse(
            {"error": "object_type is required"},
            status=400,
        )

    if not query:
        return JsonResponse({"data": {"suggestions": []}})

    logger.debug("Search suggest for %r with query %r", object_type, query)

    user = request.user
    if not user.has_perm(f"cms.view_{object_type}"):
        raise PermissionDenied

    model_cls = get_model_cls_from_object_type(object_type, language_slug)

    if not hasattr(model_cls, "search_fields") or not model_cls.search_fields:
        return JsonResponse(
            {"error": f"Model {object_type} does not support search suggestions"},
            status=400,
        )

    # Get region filter field for this object type
    region_filter_field = REGION_FILTER_FIELDS.get(object_type)

    suggestions = suggest_tokens_for_model(
        model_cls,
        query=query,
        region=request.region,
        region_filter_field=region_filter_field,
    )

    # Sort by score descending and limit results
    sorted_suggestions = sorted(
        suggestions.get("suggestions", []),
        key=lambda item: item["score"],
        reverse=True,
    )[:MAX_RESULT_COUNT]

    return JsonResponse({"data": {"suggestions": sorted_suggestions}})
