"""
This module includes functions related to the imprint API endpoint.
"""
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.html import strip_tags

from ..decorators import json_response

logger = logging.getLogger(__name__)


def transform_imprint(imprint_translation):
    """
    Function to create a JSON from a single imprint_translation object.

    :param imprint_translation: single page translation object
    :type imprint_translation: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :return: data necessary for API
    :rtype: dict
    """
    absolute_url = imprint_translation.get_absolute_url()
    return {
        "id": imprint_translation.id,
        "url": settings.BASE_URL + absolute_url,
        "path": absolute_url,
        "title": imprint_translation.title,
        "modified_gmt": imprint_translation.last_updated,
        "excerpt": strip_tags(imprint_translation.content),
        "content": imprint_translation.content,
        "parent": None,
        "available_languages": imprint_translation.available_languages,
        "thumbnail": None,
        "hash": None,
    }


@json_response
# pylint: disable=unused-argument
def imprint(request, region_slug, language_slug):
    """
    Get imprint for language and return JSON object to client. If no imprint translation
    is available in the selected language, try to return the translation in the region
    default language.

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str

    :return: JSON object according to APIv3 imprint endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = request.region
    # Check if an imprint is available for that region
    if region.imprint:
        imprint_translation = region.imprint.get_public_translation(language_slug)
        if imprint_translation:
            return JsonResponse(transform_imprint(imprint_translation))
        if region.default_language:
            imprint_default_translation = region.imprint.get_public_translation(
                region.default_language.slug
            )
            if imprint_default_translation:
                return JsonResponse(transform_imprint(imprint_default_translation))
    # If imprint does not exist, return an empty response. Turn off Safe-Mode to allow serializing arrays
    logger.info(
        "The imprint for region %r in the language %s does not exist",
        region,
        language_slug,
    )
    return JsonResponse([], safe=False)
