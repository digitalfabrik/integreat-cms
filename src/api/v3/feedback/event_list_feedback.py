from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import EventListFeedback


@feedback_handler
# pylint: disable=unused-argument
def event_list_feedback(data, region, language, comment, emotion, is_technical):
    EventListFeedback.objects.create(
        region=region,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
