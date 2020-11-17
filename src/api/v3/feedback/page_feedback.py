"""
APIv3 endpoint for feedback bout single pages
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from api.decorators import feedback_handler
from cms.models import PageFeedback, PageTranslation


@feedback_handler
def page_feedback(data, region, language, comment, emotion, is_technical):
    """
    Decorate function for storing feedback about single page in database

    :param data: HTTP request body data
    :type data: dict
    :param region: The region of this sitemap's urls
    :type region: ~cms.models.regions.region.Region
    :param language: The language of this sitemap's urls
    :type language: ~cms.models.languages.language.Language
    :param comment: The comment sent as feedback
    :type comment: str
    :param emotion: up or downvote, neutral
    :type emotion: str
    :param is_technical: is feedback on content or on tech
    :type is_technical: bool

    :return: decorated function that saves feedback in database
    :rtype: ~collections.abc.Callable
    """
    return page_feedback_internal(
        data, region, language, comment, emotion, is_technical
    )


def page_feedback_internal(data, region, language, comment, emotion, is_technical):
    """
    Store feedback about single event in database

    :param data: HTTP request body data
    :type data: dict
    :param region: The region of this sitemap's urls
    :type region: ~cms.models.regions.region.Region
    :param language: The language of this sitemap's urls
    :type language: ~cms.models.languages.language.Language
    :param comment: The comment sent as feedback
    :type comment: str
    :param emotion: up or downvote, neutral
    :type emotion: str
    :param is_technical: is feedback on content or on tech
    :type is_technical: bool

    :return: JSON object according to APIv3 single page feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    page = get_object_or_404(
        PageTranslation, page__region=region, language=language, slug=data.get("slug")
    ).page

    PageFeedback.objects.create(
        page=page,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
