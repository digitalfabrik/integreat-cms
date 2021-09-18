from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ....cms.models import POIFeedback, POITranslation
from ...decorators import json_response, feedback_handler


@feedback_handler
@json_response
def poi_feedback(data, region, language, comment, rating, is_technical):
    """
    Store feedback about single POI in database

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

    :return: decorated function that saves feedback in database
    :rtype: ~collections.abc.Callable
    """
    poi_translation = get_object_or_404(
        POITranslation, poi__region=region, language=language, slug=data.get("slug")
    )

    POIFeedback.objects.create(
        poi_translation=poi_translation,
        region=region,
        language=language,
        rating=rating,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
