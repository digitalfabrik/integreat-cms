"""
APIv3 endpoint for feedback about the imprint
"""
from django.http import JsonResponse

from ....cms.models.feedback.imprint_page_feedback import ImprintPageFeedback
from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
def imprint_page_feedback(data, region, language, comment, rating, is_technical):
    """
    Store feedback about imprint in database

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
    return imprint_page_feedback_internal(
        data, region, language, comment, rating, is_technical
    )


# pylint: disable=unused-argument
def imprint_page_feedback_internal(
    data, region, language, comment, rating, is_technical
):
    """
    Store feedback about imprint in database

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

    :return: JSON object according to APIv3 imprint feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    ImprintPageFeedback.objects.create(
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
