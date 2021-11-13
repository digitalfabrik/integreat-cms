"""
APIv3 legacy feedback endpoint for pages, events and imprint
"""
from django.conf import settings
from django.http import JsonResponse

from .event_feedback import event_feedback_internal
from .imprint_page_feedback import imprint_page_feedback_internal
from .page_feedback import page_feedback_internal

from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
def legacy_feedback_endpoint(data, region, language, comment, rating, is_technical):
    """
    Decorate function for storing feedback about single page, imprint or event in database. This
    is a legacy endpoint for compatibility.

    :param data: HTTP request body data
    :type data: dict

    :param region: The region of this sitemap's urls
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param language: The language of this sitemap's urls
    :type language: ~integreat_cms.cms.models.languages.language.Language

    :param comment: The comment sent as feedback
    :type comment: str

    :param rating: up or downvote, neutral
    :type rating: str

    :param is_technical: is feedback on content or on tech
    :type is_technical: bool

    :return: decorated function that saves feedback in database
    :rtype: ~collections.abc.Callable
    """
    link = data.get("permalink")
    if not link:
        return JsonResponse({"error": "Link is required."}, status=400)
    link_components = list(filter(None, link.split("/")))
    if link_components[-1] == settings.IMPRINT_SLUG:
        return imprint_page_feedback_internal(
            data, region, language, comment, rating, is_technical
        )
    data["slug"] = link_components[-1]
    if link_components[-2] == "events":
        return event_feedback_internal(
            data, region, language, comment, rating, is_technical
        )
    return page_feedback_internal(data, region, language, comment, rating, is_technical)
