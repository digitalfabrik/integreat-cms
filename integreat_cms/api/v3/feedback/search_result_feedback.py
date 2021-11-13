"""
APIv3 app search result feedback endpoint
"""
from django.http import JsonResponse

from ....cms.models import SearchResultFeedback
from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
# pylint: disable=unused-argument
def search_result_feedback(data, region, language, comment, rating, is_technical):
    """
    Store feedback on app search results in database

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

    :return: JSON object according to APIv3 search result feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    query = data.get("query")
    if not query:
        return JsonResponse({"error": "Search query is required."}, status=400)
    SearchResultFeedback.objects.create(
        search_query=query,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
