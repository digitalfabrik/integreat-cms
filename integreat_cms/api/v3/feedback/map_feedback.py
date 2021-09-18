"""
APIv3 endpoint for the map (POIs in general)
"""
from django.http import JsonResponse

from ....cms.models import MapFeedback
from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
# pylint: disable=unused-argument
def map_feedback(data, region, language, comment, rating, is_technical):
    """
    Store feedback on map in database

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

    :return: JSON object according to APIv3 event list feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    MapFeedback.objects.create(
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
