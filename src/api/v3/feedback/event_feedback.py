from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import EventFeedback, EventTranslation


@feedback_handler
def event_feedback(data, region, language, comment, emotion, is_technical):
    return event_feedback_internal(
        data, region, language, comment, emotion, is_technical
    )


def event_feedback_internal(data, region, language, comment, emotion, is_technical):
    event_slug = data.get("slug")
    print(event_slug)
    if not event_slug:
        return JsonResponse({"error": "Event slug is required."}, status=400)
    try:
        event = EventTranslation.objects.get(
            event__region=region, language=language, slug=event_slug
        ).event
        EventFeedback.objects.create(
            event=event,
            language=language,
            emotion=emotion,
            comment=comment,
            is_technical=is_technical,
        )
        return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
    except EventTranslation.DoesNotExist:
        return JsonResponse(
            {"error": f'No event found with slug "{event_slug}"'}, status=404
        )
