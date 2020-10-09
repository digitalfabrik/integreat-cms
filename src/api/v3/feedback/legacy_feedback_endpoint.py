from django.http import JsonResponse

from api.decorators import feedback_handler
from api.v3.feedback.event_feedback import event_feedback_internal
from api.v3.feedback.imprint_page_feedback import imprint_page_feedback_internal
from api.v3.feedback.page_feedback import page_feedback_internal
from backend.settings import IMPRINT_SLUG


@feedback_handler
def legacy_feedback_endpoint(data, region, language, comment, emotion, is_technical):
    link = data.get("permalink")
    if not link:
        return JsonResponse({"error": f"Link is required."}, status=400)
    link_components = list(filter(None, link.split("/")))
    if link_components[-1] == IMPRINT_SLUG:
        return imprint_page_feedback_internal(
            data, region, language, comment, emotion, is_technical
        )
    data["slug"] = link_components[-1]
    if link_components[-2] == "events":
        return event_feedback_internal(
            data, region, language, comment, emotion, is_technical
        )
    else:
        return page_feedback_internal(
            data, region, language, comment, emotion, is_technical
        )
