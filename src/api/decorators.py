from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def feedback_handler(func):
    @csrf_exempt
    def handle_feedback(request, region_slug, language_code):
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request."}, status=405)

        data = request.POST.dict()
        comment = data.pop("comment", "")
        rating = data.pop("rating", None)
        category = data.pop("category", None)

        if rating not in [None, "up", "down"]:
            return JsonResponse({"error": "Invalid rating."}, status=400)
        if comment == "" and not rating:
            return JsonResponse(
                {"error": "Either comment or rating is required."}, status=400
            )
        if rating == "up":
            emotion = "Pos"
        elif rating == "down":
            emotion = "Neg"
        else:
            emotion = "NA"
        is_technical = category == "Technisches Feedback"
        return func(data, region_slug, language_code, comment, emotion, is_technical)

    return handle_feedback
