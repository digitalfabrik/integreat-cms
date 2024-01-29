"""
This module includes functions related to the pages API endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import prefetch_related_objects
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from ...cms.forms import PageTranslationForm
from ...cms.models import Page
from ..decorators import json_response, matomo_tracking
from .offers import transform_offer

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

    from ...cms.models import PageTranslation

logger = logging.getLogger(__name__)


def transform_page(page_translation: PageTranslation) -> dict[str, Any]:
    """
    Function to create a dict from a single page_translation Object.

    :param page_translation: single page translation object
    :raises ~django.http.Http404: HTTP status 404 if a parent is archived

    :return: data necessary for API
    """
    fallback_parent = {
        "id": 0,
        "url": None,
        "path": None,
    }

    parent_page = page_translation.page.cached_parent
    if parent_page and not parent_page.explicitly_archived:
        if parent_public_translation := parent_page.get_public_translation(
            page_translation.language.slug
        ):
            parent_absolute_url = parent_public_translation.get_absolute_url()
            parent = {
                "id": parent_page.id,
                "url": settings.BASE_URL + parent_absolute_url,
                "path": parent_absolute_url,
            }
            # use left edge indicator of mptt model for ordering of child pages
            order = page_translation.page.lft
        else:
            logger.info(
                "The parent %r of %r does not have a public translation in %r",
                parent_page,
                page_translation.page,
                page_translation.language,
            )
            raise Http404("No Page matches the given url or id.")
    else:
        parent = fallback_parent
        # use tree id of mptt model for ordering of root pages
        order = page_translation.page.tree_id

    organization = page_translation.page.organization
    absolute_url = page_translation.get_absolute_url()
    return {
        "id": page_translation.id,
        "url": settings.BASE_URL + absolute_url,
        "path": absolute_url,
        "title": page_translation.title,
        "modified_gmt": page_translation.combined_last_updated,  # deprecated field in the future
        "last_updated": timezone.localtime(page_translation.combined_last_updated),
        "excerpt": strip_tags(page_translation.combined_text),
        "content": page_translation.combined_text,
        "parent": parent,
        "order": order,
        "available_languages": page_translation.available_languages_dict,
        "thumbnail": (
            page_translation.page.icon.url if page_translation.page.icon else None
        ),
        "organization": (
            {
                "id": organization.id,
                "slug": organization.slug,
                "name": organization.name,
                "logo": organization.icon.url,
                "website": organization.website,
            }
            if organization
            else None
        ),
        "hash": None,
        "embedded_offers": [
            transform_offer(offer, page_translation.page.region)
            for offer in page_translation.page.embedded_offers.all()
        ],
    }


@matomo_tracking
@json_response
# pylint: disable=unused-argument
def pages(request: HttpRequest, region_slug: str, language_slug: str) -> JsonResponse:
    """
    Function to iterate through all non-archived pages of a region and return them as JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON object according to APIv3 pages endpoint definition
    """
    region = request.region
    # Throw a 404 error when the language does not exist or is disabled
    region.get_language_or_404(language_slug, only_active=True)
    result = []
    # The preliminary filter for explicitly_archived=False is not strictly required, but reduces the number of entries
    # requested from the database
    for page in (
        region.pages.select_related("organization__icon")
        .prefetch_related(
            "embedded_offers",
        )
        .filter(explicitly_archived=False)
        .cache_tree(archived=False, language_slug=language_slug)
    ):
        if page_translation := page.get_public_translation(language_slug):
            result.append(transform_page(page_translation))
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


def get_single_page(request: HttpRequest, language_slug: str) -> Page:
    """
    Helper function returning the desired page or a 404 if the
    requested page does not exist or is archived.

    :param request: The request that has been sent to the Django server
    :param language_slug: Code to identify the desired language
    :raises ~django.core.exceptions.MultipleObjectsReturned: If the given url cannot be resolved unambiguously

    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :raises RuntimeError: If neither the id nor the url parameter is given

    :return: the requested page
    """
    region = request.region

    if request.GET.get("id"):
        page = get_object_or_404(region.pages, id=request.GET.get("id"))

    elif request.GET.get("url"):
        # Strip leading and trailing slashes to avoid ambiguous urls
        url = request.GET.get("url").strip("/")
        # The last path component of the url is the page translation slug
        page_translation_slug = slugify(url.split("/")[-1], allow_unicode=True)
        # Get page by filtering for translation slug and translation language slug
        filtered_pages = (
            region.pages.select_related("organization__icon")
            .prefetch_related("embedded_offers")
            .filter(
                translations__slug=page_translation_slug,
                translations__language__slug=language_slug,
            )
            .distinct()
        )

        if len(filtered_pages) > 1:
            logger.error(
                "Page translation slug %r is not unique per region and language, found multiple: %r",
                page_translation_slug,
                filtered_pages,
            )
            raise MultipleObjectsReturned(
                "This page translation slug is not unique, please contact your server administrator."
            )
        if not filtered_pages:
            raise Http404("No matching page translation found for url.")
        page = filtered_pages[0]

    else:
        raise RuntimeError("Either the id or the url parameter is required.")

    if page.explicitly_archived:
        raise Http404("No matching page translation found for url.")

    # Check if any ancestor is archived -> will raise a 404
    get_public_ancestor_translations(page, language_slug)

    return page


@json_response
# pylint: disable=unused-argument
def single_page(
    request: HttpRequest, region_slug: str, language_slug: str
) -> JsonResponse:
    """
    View function returning the desired page as a JSON or a 404 if the
    requested page does not exist.

    :param request: The request that has been sent to the Django server
    :param region_slug: Slug defining the region
    :param language_slug: Code to identify the desired language
    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: JSON with the requested page and a HTTP status 200.
    """
    try:
        page = get_single_page(request, language_slug)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    if page_translation := page.get_public_translation(language_slug):
        return JsonResponse(transform_page(page_translation), safe=False)

    raise Http404("No Page matches the given url or id.")


@matomo_tracking
@json_response
def children(
    request: HttpRequest, region_slug: str, language_slug: str
) -> JsonResponse:
    """
    Retrieves all children for a single page

    :param request: The request that has been sent to the Django server
    :param region_slug: Slug defining the region
    :param language_slug: Code to identify the desired language
    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: JSON with the requested page descendants
    """

    depth = int(request.GET.get("depth", 1))
    try:
        # try to get a single ancestor page based on the requests query string
        root_pages = [get_single_page(request, language_slug)]
    except RuntimeError:
        # if neither id nor url is set then get all root pages
        root_pages = Page.get_root_pages(region_slug)
        # simulate a virtual root node for WP compatibility
        # so that depth = 1 returns only those pages without parents (immediate children of this virtual root page)
        # like in wordpress depth = 0 will return no results in this case
        depth -= 1
    result = []
    public_region_pages = (
        request.region.pages.select_related("organization__icon")
        .prefetch_related("embedded_offers")
        .filter(
            explicitly_archived=False, tree_id__in=[page.tree_id for page in root_pages]
        )
        .cache_tree(archived=False, language_slug=language_slug)
    )
    for root in root_pages:
        descendants = root.get_tree_max_depth(max_depth=depth)
        for descendant in public_region_pages:
            if descendant in descendants:
                result.append(
                    transform_page(descendant.get_public_translation(language_slug))
                )
    return JsonResponse(result, safe=False)


@json_response
# pylint: disable=unused-argument
def parents(request: HttpRequest, region_slug: str, language_slug: str) -> JsonResponse:
    """
    Retrieves all ancestors (parent and all nodes up to the root node) of a page.
    If any ancestor is archived, an 404 is raised.

    :param request: The request that has been sent to the Django server
    :param region_slug: Slug defining the region
    :param language_slug: Code to identify the desired language
    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: JSON with the requested page ancestors
    """
    try:
        current_page = get_single_page(request, language_slug)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    if not current_page.get_public_translation(language_slug):
        raise Http404("No Page matches the given url or id.")
    result = get_public_ancestor_translations(current_page, language_slug)
    return JsonResponse(result, safe=False)


def get_public_ancestor_translations(
    current_page: Page, language_slug: str
) -> list[dict[str, Any]]:
    """
    Retrieves all ancestors (parent and all nodes up to the root node) of a page.
    If any ancestor is archived or has a missing translation, a 404 is raised.

    :param current_page: the page that needs a list of its ancestor translations
    :param language_slug: Code to identify the desired language
    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: JSON with the requested page ancestors
    """
    result = []
    cached_ancestors = current_page.get_cached_ancestors()
    prefetch_related_objects(cached_ancestors, "organization")
    for ancestor in cached_ancestors:
        public_translation = ancestor.get_public_translation(language_slug)
        if not public_translation or ancestor.explicitly_archived:
            raise Http404("No Page matches the given url or id.")
        result.append(transform_page(public_translation))
    return result


@csrf_exempt
@json_response
# pylint: disable=unused-argument
def push_page_translation_content(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Retrieves all ancestors (parent and all nodes up to the root node) of a page

    :param request: The request that has been sent to the Django server
    :param region_slug: Slug defining the region
    :param language_slug: Code to identify the desired language
    :raises ~django.http.Http404: HTTP status 404 if the request is malformed or no page with the given id or url exists.

    :return: JSON with the requested page ancestors
    """
    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError as e:
        logger.error("Push Content: failed to parse JSON: %s", e)
        return JsonResponse({"status": "error"}, status=405)

    if not all(key in data for key in ["content", "token"]):
        logger.error("Push Content: missing required key.")
        return JsonResponse({"status": "error"}, status=405)

    page = request.region.pages.filter(api_token=data["token"]).first()
    if not page or not data["token"]:
        return JsonResponse(data={"status": "denied"}, status=403)

    translation = page.get_translation(language_slug)
    data = {
        "content": data["content"],
        "title": translation.title,
        "slug": translation.slug,
        "status": translation.status,
        "minor_edit": False,
    }
    page_translation_form = PageTranslationForm(
        data=data,
        instance=translation,
        additional_instance_attributes={
            "page": page,
            "creator": None,
        },
    )
    if page_translation_form.is_valid():
        page_translation_form.save()
        return JsonResponse({"status": "success"})
    logger.error("Push Content: failed to validate page translation.")
    return JsonResponse({"status": "error"}, status=405)
