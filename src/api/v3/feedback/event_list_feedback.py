"""
APIv3 endpoint for the events (list)
"""
from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import EventListFeedback


@feedback_handler
# pylint: disable=unused-argument
def event_list_feedback(data, region, language, comment, emotion, is_technical):
    """
    Store feedback on events list in database

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

    :return: JSON object according to APIv3 event list feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    EventListFeedback.objects.create(
        region=region,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
