from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ...models.mixins import SearchSuggestMixin
from ...search.suggest import suggest_tokens_for_model

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)

# The maximum number of results returned by `search_content_ajax`
MAX_RESULT_COUNT: int = 20


CONTENT_TYPES = [
    "contact",
    "feedback",
    "language",
    "mediafile",
    "organization",
    "region",
    "user",
]
TRANSLATION_CONTENT_TYPES = ["event", "page", "poi", "pushnotification"]


@require_POST
def search_suggest(
    request: HttpRequest,
    region_slug: str | None = None,
    language_slug: str | None = None,
) -> JsonResponse:
    """Searches all pois, events and pages for the current region and returns all that
    match the search query. Results which match the query in the title or slug get ranked
    higher than results which only match through their text content.

    :param request: The current request
    :param language_slug: language slug
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If the user has no permission to the object type

    :raises AttributeError: If the request contains an object type which is unknown or if the user has no permission for it

    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    """

    body = json.loads(request.body.decode("utf-8"))
    query = body["query_string"]
    object_types = set(body.get("object_types", []))

    logger.debug("Ajax call: Live search for %r with query %r", object_types, query)

    user = request.user

    for object_type in object_types:
        if object_type not in CONTENT_TYPES + TRANSLATION_CONTENT_TYPES:
            raise AttributeError(f"Unexpected object type(s): {object_types}")

        if not user.has_perm(f"cms.view_{object_type}"):
            raise PermissionDenied

        if object_type in TRANSLATION_CONTENT_TYPES and not language_slug:
            raise AttributeError("Language slug is not provided")

        if object_type in CONTENT_TYPES or object_type == "page":
            model_cls = apps.get_model("cms", object_type)
        else:
            translation_object_type = f"{object_type}translation"
            model_cls = apps.get_model("cms", translation_object_type)

        if model_cls is None:
            return JsonResponse({"results": []})

        if not issubclass(model_cls, SearchSuggestMixin):
            return JsonResponse({"results": []}, status=400)

    suggestions = suggest_tokens_for_model(model_cls, query=query)
    # sort by score
    suggestions["suggestions"].sort(key=lambda item: item["score"], reverse=True)

    return JsonResponse({"data": suggestions})
