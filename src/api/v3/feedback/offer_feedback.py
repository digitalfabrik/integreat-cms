"""
APIv3 feedback endpoint for feedback about single offer
"""
from django.http import JsonResponse

from api.decorators import feedback_handler
from cms.models import OfferFeedback, Offer


@feedback_handler
# pylint: disable=unused-argument
def offer_feedback(data, region, language, comment, emotion, is_technical):
    """
    Store feedback about single offer in database

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

    :return: JSON object according to APIv3 offer feedback endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    offer_slug = data.get("slug", None)
    if not offer_slug:
        return JsonResponse({"error": "Offer slug is required."}, status=400)
    offer = Offer.objects.filter(region=region, template__slug=offer_slug).first()
    if offer is None:
        return JsonResponse(
            {"error": f'No offer found with slug "{offer_slug}"'}, status=404
        )

    OfferFeedback.objects.create(
        offer=offer,
        language=language,
        emotion=emotion,
        comment=comment,
        is_technical=is_technical,
    )
    return JsonResponse({"success": "Feedback successfully submitted"}, status=201)
