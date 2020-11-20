"""
pages API endpoint
"""
from django.http import JsonResponse

from backend.settings import BASE_URL
from cms.models import Region

from ..decorators import json_response


def transform_page(page_translation):
    """
    Function to create a JSON from a single page_translation Object.

    :param page_translation: single page translation object
    :type page_translation: ~cms.models.pages.page_translation.PageTranslation

    :return: return data necessary for API
    :rtype: dict
    """
    if page_translation.page.icon:
        thumbnail = BASE_URL + page_translation.page.icon.url
    else:
        thumbnail = None
    if page_translation.page.parent:
        parent = {
            "id": page_translation.page.parent.id,
            "url": page_translation.page.parent.get_translation(
                page_translation.language.code
            ).permalink,
            "path": page_translation.page.parent.get_translation(
                page_translation.language.code
            ).slug,
        }
    else:
        parent = None
    return {
        "id": page_translation.id,
        "url": page_translation.permalink,
        "path": page_translation.slug,
        "title": page_translation.title,
        "modified_gmt": page_translation.last_updated,
        "excerpt": page_translation.text,
        "content": page_translation.combined_text,
        "parent": parent,
        "order": page_translation.page.lft,  # use left edge indicator of mptt model for order
        "available_languages": page_translation.available_languages,
        "thumbnail": thumbnail,
        "hash": None,
    }


@json_response
# pylint: disable=unused-argument
def pages(request, region_slug, language_code):
    """
    Function to iterate through all pages related to a region and adds them to a JSON.

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str
    :param language_code: language code
    :type language_code: str

    :return: JSON object according to APIv3 pages endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)
    result = []
    for page in region.pages.filter(archived=False, parent=None):  # get main level
        page_translation = page.get_public_translation(language_code)
        if page_translation:
            result.append(transform_page(page_translation))
            result = get_children(page, language_code, result)
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


def get_children(parent, language_code, result):
    for page in parent.children.filter(archived=False):
        page_translation = page.get_public_translation(language_code)
        if page_translation:
            result.append(transform_page(page_translation))
            result = get_children(page, language_code, result)
    return result
