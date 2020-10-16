"""
APIv3 endpoint for feedback about the imprint
"""
from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models.feedback.imprint_page_feedback import ImprintPageFeedback


@feedback_handler
def imprint_page_feedback(data, region, language, comment, emotion, is_technical):
    """
    Store feedback about imprint in database

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
    :rtype: func
    """
    return imprint_page_feedback_internal(
        data, region, language, comment, emotion, is_technical
    )


# pylint: disable=unused-argument
def imprint_page_feedback_internal(
    data, region, language, comment, emotion, is_technical
):
    """
    Store feedback about imprint in database

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

    :return: JSON object according to APIv3 imprint feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    ImprintPageFeedback.objects.create(
        region=region,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
