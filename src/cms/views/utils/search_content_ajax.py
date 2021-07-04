import logging
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from backend.settings import WEBAPP_URL
from ...constants import status
from ...decorators import region_permission_required
from ...models import Region, EventTranslation, PageTranslation, POITranslation

logger = logging.getLogger(__name__)

# The maximum number of results returned by `search_content_ajax`
MAX_RESULT_COUNT = 20


def format_object_translation(object_translation, typ):
    """
    Formats the [poi/event/page]-translation as json

    :param object_translation: A translation object which has a title and a permalink
    :type object_translation: ~cms.models.events.event.Event or ~cms.models.pages.page.Page or ~cms.models.pois.poi.POI
    :param typ: The type of this object
    :type typ: str
    :return: A dictionary with the title, url and type of the translation object
    :rtype: dict
    """
    return {
        "title": object_translation.title,
        "url": f"{WEBAPP_URL}/{object_translation.permalink}",
        "type": typ,
    }


def find_objects(manager, obj_type, region, language_slug, query, hierarchical=False):
    """
    Filters all object translations from ``manager`` of this language that match the ``query``

    :param manager: The manager for a specific model
    :type manager: ~django.db.models.Manager
    :param obj_type: The content type of the queried translations
    :type obj_type: str
    :param region: The current region
    :type region: ~cms.models.regions.region.Region
    :param language_slug: The language slug
    :type language_slug: str
    :param query: The query string used for filtering the objects
    :type query: str
    :param hierarchical: Whether or not the given model is hiearchical (which impacts the method for filtering out
                         archived results)
    :type hierarchical: bool
    :return: A list of translation objects (formatted as dict)
    :rtype: list [ dict ]
    """
    archived_flag = "explicitly_archived" if hierarchical else "archived"
    result = (
        manager.objects.filter(
            **{
                obj_type + "__region": region,
                obj_type + "__" + archived_flag: False,
                "language__slug": language_slug,
                "status": status.PUBLIC,
            }
        )
        .filter(Q(slug__icontains=query) | Q(title__icontains=query))
        .distinct(obj_type)
    )
    # If the object type is hierarchical, filter out implicitly archived objects (objects with archived ancestors)
    if hierarchical:
        result = filter(lambda x: not getattr(x, obj_type).implicitly_archived, result)
    return [format_object_translation(obj, obj_type) for obj in result]


@require_POST
@login_required
@region_permission_required
# pylint: disable=unused-argument
def search_content_ajax(request, region_slug, language_slug):
    """Searches all pois, events and pages for the current region and returns all that
    match the search query. Results which match the query in the title or slug get ranked
    higher than results which only match through their text content.

    :param request: The current request
    :type request: ~django.http.HttpResponse
    :param region_slug: region identifier
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str
    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    :rtype: ~django.http.JsonResponse
    """

    region = Region.get_current_region(request)
    query = json.loads(request.body.decode("utf-8"))["query_string"]

    logger.debug(
        "Ajax call: Live search for pois, events and pages with query %r", query
    )

    results = []

    user = request.user
    if user.has_perm("cms.view_event"):
        results.extend(
            find_objects(EventTranslation, "event", region, language_slug, query)
        )

    if user.has_perm("cms.view_page"):
        results.extend(
            find_objects(
                PageTranslation, "page", region, language_slug, query, hierarchical=True
            )
        )

    if user.has_perm("cms.view_poi"):
        results.extend(
            find_objects(POITranslation, "poi", region, language_slug, query)
        )

    # sort alphabetically by title
    results.sort(key=lambda k: k["title"])

    return JsonResponse({"data": results[:MAX_RESULT_COUNT]})
