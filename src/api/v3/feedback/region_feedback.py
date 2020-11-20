"""
APIv3 endpoint for feedback about full region (main level of content)
"""
from django.http import JsonResponse

from cms.models import RegionFeedback

from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
# pylint: disable=unused-argument
def region_feedback(data, region, language, comment, emotion, is_technical):
    """
    Store feedback about region / main pages in database

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

    :return: JSON object according to APIv3 region feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    RegionFeedback.objects.create(
        region=region,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
