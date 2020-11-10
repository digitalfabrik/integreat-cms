from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import EventFeedback, EventTranslation


@feedback_handler
def event_feedback(data, region, language, comment, emotion, is_technical):
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

    :return: decorated function that saves feedback in database
    :rtype: ~collections.abc.Callable
    """
    return event_feedback_internal(
        data, region, language, comment, emotion, is_technical
    )


def event_feedback_internal(data, region, language, comment, emotion, is_technical):
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
    event_slug = data.get("slug")
    if not event_slug:
        return JsonResponse({"error": "Event slug is required."}, status=400)
    try:
        event_translation = EventTranslation.objects.get(
            event__region=region, language=language, slug=event_slug
        )
    except EventTranslation.DoesNotExist:
        return JsonResponse(
            {"error": f'No event found with slug "{event_slug}"'}, status=404
        )
    EventFeedback.objects.create(
        event_translation=event_translation,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
