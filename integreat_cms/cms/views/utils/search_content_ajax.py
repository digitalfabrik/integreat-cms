import logging
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ...constants import status
from ...utils.user_utils import search_users
from ...models import (
    Region,
    EventTranslation,
    POITranslation,
    Feedback,
    PushNotificationTranslation,
    MediaFile,
    Directory,
)

logger = logging.getLogger(__name__)

# The maximum number of results returned by `search_content_ajax`
MAX_RESULT_COUNT = 20


def format_object_translation(object_translation, typ):
    """
    Formats the [poi/event/page]-translation as json

    :param object_translation: A translation object which has a title and a permalink
    :type object_translation: ~integreat_cms.cms.models.events.event.Event or ~integreat_cms.cms.models.pages.page.Page or ~integreat_cms.cms.models.pois.poi.POI
    :param typ: The type of this object
    :type typ: str
    :return: A dictionary with the title, url and type of the translation object
    :rtype: dict
    """
    return {
        "title": object_translation.title,
        "url": f"{settings.WEBAPP_URL}{object_translation.get_absolute_url()}",
        "type": typ,
    }


@require_POST
# pylint: disable=unused-argument
def search_content_ajax(request, region_slug=None, language_slug=None):
    """Searches all pois, events and pages for the current region and returns all that
    match the search query. Results which match the query in the title or slug get ranked
    higher than results which only match through their text content.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: language slug
    :type language_slug: str

    :raises AttributeError: If the request contains an object type which is unknown or if the user has no permission for it

    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    :rtype: ~django.http.JsonResponse
    """

    region = request.region
    body = json.loads(request.body.decode("utf-8"))
    query = body["query_string"]
    # whether to return only archived object, ignored if not applicable
    archived_flag = body["archived"]
    object_types = set(body.get("object_types", []))

    logger.debug("Ajax call: Live search for %r with query %r", object_types, query)

    results = []

    user = request.user
    if user.has_perm("cms.view_event") and "event" in object_types:
        object_types.remove("event")
        event_translations = (
            EventTranslation.search(region, language_slug, query)
            .filter(event__archived=archived_flag, status=status.PUBLIC)
            .select_related("event__region", "language")
        )
        results.extend(
            format_object_translation(obj, "event") for obj in event_translations
        )

    if user.has_perm("cms.view_feedback") and "feedback" in object_types:
        object_types.remove("feedback")
        results.extend(
            {
                "title": feedback.comment,
                "url": None,
                "type": "feedback",
            }
            for feedback in Feedback.search(region, query)
        )

    if user.has_perm("cms.view_page") and "page" in object_types:
        object_types.remove("page")
        pages = region.pages.all().cache_tree(archived=archived_flag)
        for page in pages:
            page_translation = page.get_translation(language_slug)
            if page_translation and (
                query.lower() in page_translation.slug
                or query.lower() in page_translation.title.lower()
            ):
                results.append(format_object_translation(page_translation, "page"))

    if user.has_perm("cms.view_poi") and "poi" in object_types:
        object_types.remove("poi")
        poi_translations = (
            POITranslation.search(region, language_slug, query)
            .filter(poi__archived=archived_flag, status=status.PUBLIC)
            .select_related("poi__region", "language")
        )
        results.extend(
            format_object_translation(obj, "poi") for obj in poi_translations
        )

    if (
        user.has_perm("cms.view_pushnotification")
        and "push_notification" in object_types
    ):
        object_types.remove("push_notification")
        results.extend(
            {
                "title": push_notification.title,
                "url": None,
                "type": "push_notification",
            }
            for push_notification in PushNotificationTranslation.search(
                region, language_slug, query
            )
        )

    if user.has_perm("cms.view_region") and "region" in object_types:
        object_types.remove("region")
        results.extend(
            {
                "title": region.name,
                "url": None,
                "type": "region",
            }
            for region in Region.search(query)
        )

    if user.has_perm("cms.view_user") and "user" in object_types:
        object_types.remove("user")
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
