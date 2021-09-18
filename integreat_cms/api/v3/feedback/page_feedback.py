"""
APIv3 endpoint for feedback bout single pages
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ....cms.models import PageFeedback, PageTranslation
from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
def page_feedback(data, region, language, comment, rating, is_technical):
    """
    Decorate function for storing feedback about single page in database

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
    return page_feedback_internal(data, region, language, comment, rating, is_technical)


def page_feedback_internal(data, region, language, comment, rating, is_technical):
    """
    Store feedback about single event in database

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

    :return: JSON object according to APIv3 single page feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """

    page_translation = get_object_or_404(
        PageTranslation, page__region=region, language=language, slug=data.get("slug")
    )

    PageFeedback.objects.create(
        page_translation=page_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
