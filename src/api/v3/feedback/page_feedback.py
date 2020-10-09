from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import PageFeedback, PageTranslation


@feedback_handler
def page_feedback(data, region, language, comment, emotion, is_technical):
    return page_feedback_internal(
        data, region, language, comment, emotion, is_technical
    )


def page_feedback_internal(data, region, language, comment, emotion, is_technical):
    page_slug = data.get("slug")
    if not page_slug:
        return JsonResponse({"error": "Page slug is required."}, status=400)
    try:
        page = PageTranslation.objects.get(
            page__region=region, language=language, slug=page_slug
        ).page
        PageFeedback.objects.create(
            page=page,
            language=language,
            emotion=emotion,
            comment=comment,
            is_technical=is_technical,
        )
        return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
    except PageTranslation.DoesNotExist:
        return JsonResponse(
            {"error": f'No page found with slug "{page_slug}"'}, status=404
        )
