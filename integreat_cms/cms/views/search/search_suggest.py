from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .utils import get_model_cls_from_object_type
from ...models.mixins import SearchSuggestMixin
from ...search.suggest import suggest_tokens_for_model

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)

# The maximum number of suggestions returned by `search_suggest`
MAX_RESULT_COUNT: int = 20


@require_POST
def search_suggest(
    request: HttpRequest,
    region_slug: str | None = None,
    language_slug: str | None = None,
) -> JsonResponse:
    """
    Provides a list of search term suggestions based on a search query.

    :param request: The current request
    :param language_slug: language slug
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If the user has no permission to the object type

    :raises AttributeError: If the request contains an object type which is unknown or if the user has no permission for it

    :return: Json object containing a list of search suggestions as {"suggestions": {"suggestion": str, "score": float}}
    """

    body = json.loads(request.body.decode("utf-8"))
    query = body["query_string"]
    object_type = body.get("object_type")

    logger.debug(f"Ajax call: Search suggest for {object_type} with query {query}")

    user = request.user

    if not user.has_perm(f"cms.view_{object_type}"):
        raise PermissionDenied

    model_cls = get_model_cls_from_object_type(object_type, language_slug)

    if model_cls is None:
        return JsonResponse({"results": []})

    if not issubclass(model_cls, SearchSuggestMixin):
        return JsonResponse({"results": []}, status=400)

    # todo only search for tokens in specified region?
    suggestions = suggest_tokens_for_model(model_cls, query=query)

    # sort by score
    suggestions["suggestions"] = sorted(
        suggestions["suggestions"],
        key=lambda item: item["score"],
        reverse=True
    )[:MAX_RESULT_COUNT]

    return JsonResponse({"data": suggestions})
