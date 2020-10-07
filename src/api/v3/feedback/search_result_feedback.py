from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import SearchResultFeedback


@feedback_handler
# pylint: disable=unused-argument
def search_result_feedback(data, region, language, comment, emotion, is_technical):
    query = data.get("query")
    if not query:
        return JsonResponse({"error": "Search query is required."}, status=400)
    SearchResultFeedback.objects.create(
        searchQuery=query,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
