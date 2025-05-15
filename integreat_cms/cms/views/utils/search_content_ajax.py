from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from lxml.html import tostring

from ...constants import region_status, status
from ...models import (
    Contact,
    Directory,
    EventTranslation,
    Feedback,
    Language,
    MediaFile,
    Organization,
    POITranslation,
    PushNotificationTranslation,
    Region,
)
from ...utils.user_utils import search_users

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.http import HttpRequest

    from ...models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)

# The maximum number of results returned by `search_content_ajax`
MAX_RESULT_COUNT: int = 20


def format_object_translation(
    object_translation: AbstractContentTranslation,
    typ: Literal["page", "event", "poi"],
    target_language_slug: str,
) -> dict:
    """
    Formats the [poi/event/page]-translation as json

    :param object_translation: A translation object which has a title and a permalink
    :param typ: The type of this object
    :param target_language_slug: The slug that the object translation should ideally have
    :return: A dictionary with the title, path, url and type of the translation object
    """
    if object_translation.language.slug != target_language_slug:
        object_translation = object_translation.foreign_object.get_public_translation(
            target_language_slug,
        )
    if isinstance(object_translation.link_title, str):
        html_title = object_translation.link_title
        text_title = object_translation.link_title
    else:
        html_title = tostring(object_translation.link_title).decode("utf-8")
        text_title = (
            object_translation.link_title.text_content()
            + object_translation.link_title.tail
        )
    return {
        "path": object_translation.path(),
        "title": text_title,
        "html_title": html_title,
        "url": f"{settings.WEBAPP_URL}{object_translation.get_absolute_url()}",
        "type": typ,
    }


@require_POST
def search_content_ajax(  # noqa: PLR0915, PLR0912, C901
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

    region = request.region
    body = json.loads(request.body.decode("utf-8"))
    query = body["query_string"]
    # whether to return only archived object, ignored if not applicable
    archived_flag = body["archived"]
    object_types = set(body.get("object_types", []))

    logger.debug("Ajax call: Live search for %r with query %r", object_types, query)

    results: list[dict[str, Any]] = []

    user = request.user

    if "contact" in object_types:
        object_types.remove("contact")
        if not user.has_perm("cms.view_contact"):
            raise PermissionDenied
        results.extend(
            {
                "title": contact.name,
                "url": None,
                "type": "contact",
            }
            for contact in Contact.objects.filter(
                name__icontains=query, location__region=region, archived=archived_flag
            ).distinct()
        )
        if TYPE_CHECKING:
            assert language_slug
        results.extend(
            {
                "title": poi_translation.title,
                "url": None,
                "type": "contact",
            }
            for poi_translation in POITranslation.search(
                region, language_slug, query
            ).filter(poi__archived=False)
        )

    if "event" in object_types:
        if TYPE_CHECKING:
            assert language_slug
        object_types.remove("event")
        if not user.has_perm("cms.view_event"):
            raise PermissionDenied
        event_translations = (
            EventTranslation.search(region, language_slug, query)
            .filter(event__archived=archived_flag, status=status.PUBLIC)
            .select_related("event__region", "language")
        )
        results.extend(
            format_object_translation(obj, "event", language_slug)
            for obj in event_translations
        )

    if "feedback" in object_types:
        object_types.remove("feedback")
        if not user.has_perm("cms.view_feedback"):
            raise PermissionDenied
        results.extend(
            {
                "title": feedback.comment,
                "url": None,
                "type": "feedback",
            }
            for feedback in Feedback.search(region, query).filter(
                archived=archived_flag,
            )
        )

    if "organization" in object_types:
        object_types.remove("organization")
        if not user.has_perm("cms.view_organization"):
            raise PermissionDenied
        results.extend(
            {
                "title": organization.name,
                "url": None,
                "type": "orgaization",
            }
            for organization in Organization.search(region, query).filter(
                archived=archived_flag,
            )
        )

    if "language" in object_types:
        object_types.remove("language")
        if not user.has_perm("cms.view_language"):
            raise PermissionDenied

        results.extend(
            {
                "title": language.translated_name,
                "url": None,
                "type": "feedback",
            }
            for language in Language.search(query)
        )

    if "page" in object_types:
        if TYPE_CHECKING:
            assert language_slug
        object_types.remove("page")
        if not user.has_perm("cms.view_page"):
            raise PermissionDenied
        pages = region.pages.all().cache_tree(archived=archived_flag)
        for page in pages:
            page_translation = page.get_translation(language_slug)
            if page_translation and (
                query.lower() in page_translation.slug
                or query.lower() in page_translation.title.lower()
            ):
                results.append(
                    format_object_translation(page_translation, "page", language_slug),
                )

    if "poi" in object_types:
        if TYPE_CHECKING:
            assert language_slug
        object_types.remove("poi")
        if not user.has_perm("cms.view_poi"):
            raise PermissionDenied
        poi_translations = (
            POITranslation.search(region, language_slug, query)
            .filter(poi__archived=archived_flag, status=status.PUBLIC)
            .select_related("poi__region", "language")
        )
        results.extend(
            format_object_translation(obj, "poi", language_slug)
            for obj in poi_translations
        )

    if "push_notification" in object_types:
        if TYPE_CHECKING:
            assert language_slug
        object_types.remove("push_notification")
        if not user.has_perm("cms.view_pushnotification"):
            raise PermissionDenied
        results.extend(
            {
                "title": push_notification.title,
                "url": None,
                "type": "push_notification",
            }
            for push_notification in PushNotificationTranslation.search(
                region,
                language_slug,
                query,
            )
        )

    if "region" in object_types:
        object_types.remove("region")
        if not user.has_perm("cms.view_region"):
            raise PermissionDenied

        regions = Region.search(query)
        if archived_flag:
            regions = regions.exclude(status=region_status.ARCHIVED)
        results.extend(
            {
                "title": region.name,
                "url": None,
                "type": "region",
            }
            for region in regions
        )

    if "user" in object_types:
        object_types.remove("user")
        if not user.has_perm("cms.view_user"):
            raise PermissionDenied
        results.extend(
            {
                "title": user.username,
                "url": None,
                "type": "user",
            }
            for user in search_users(region, query)
        )

    if "media" in object_types:
        object_types.remove("media")
        results.extend(
            {
                "title": file.name,
                "url": None,
                "type": "file",
            }
            for file in MediaFile.search(region, query)
        )
        results.extend(
            {
                "title": directory.name,
                "url": None,
                "type": "directory",
            }
            for directory in Directory.search(region, query)
        )

    if object_types:
        raise AttributeError(f"Unexpected object type(s): {object_types}")

    # sort alphabetically by title
    results.sort(key=lambda k: k["title"])

    return JsonResponse({"data": results[:MAX_RESULT_COUNT]})
