from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .utils import get_model_cls_from_object_type

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

logger = logging.getLogger(__name__)

#: The maximum number of results returned by :func:`search_content_ajax`
MAX_RESULT_COUNT: int = 20


@require_POST
def search_content_ajax(
    request: HttpRequest,
    region_slug: str | None = None,
    language_slug: str | None = None,
) -> JsonResponse:
    """Searches all pois, events and pages for the current region and returns all that
    match the search query. Results which match the query in the title or slug get ranked
    higher than results which only match through their text content.

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language
    :raises ~django.core.exceptions.PermissionDenied: If the user has no permission to the object type
    :raises AttributeError: If the request contains an object type which is unknown
    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    """
    region = request.region
    body = json.loads(request.body.decode("utf-8"))
    query = body["query_string"]
    # whether to return only archived object, ignored if not applicable
    archived_flag = body.get("archived", False)
    link_suggestion_flag = body.get("is_link_suggestion", False)
    object_types = set(body.get("object_types", []))

    logger.debug("Ajax call: Live search for %r with query %r", object_types, query)

    results: list[dict[str, Any]] = []

    user = request.user

    # This function is used for the search window in a content list view and to suggest
    # targets for internal links in the "Insert link" menu in the editor.
    # For the former we only care about the plain text representation and don't want any
    # duplicates (e.g. if we have two events titled "Community kitchen" we only want one
    # suggestion to search for this string – both events will still show in the list view
    # as soon as the user submits his actual search).
    # For the latter we need the information uniquely identifying each object (such as the url).
    # `link_suggestion_flag` is set to True if we want all unique objects, even if there
    # are multiple with the same title.
    kwargs = {
        "region": region,
        "query": query,
        "archived_flag": archived_flag,
        "language_slug": language_slug,
        "link_suggestion_flag": link_suggestion_flag,
    }

    for object_type in object_types:
        if not user.has_perm(f"cms.view_{object_type}"):
            raise PermissionDenied
        model_cls = get_model_cls_from_object_type(object_type, language_slug)
        results.extend(model_cls.suggest(**kwargs))

    # sort alphabetically by title
    results.sort(key=lambda k: k["title"])

    return JsonResponse({"data": results[:MAX_RESULT_COUNT]})
