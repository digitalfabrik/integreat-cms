"""
This module includes functions related to the push notification that are sent via firebase.
"""
from django.http import JsonResponse
from django.utils.formats import date_format
from django.utils.timezone import localtime

from ...cms.models import PushNotificationTranslation
from ..decorators import json_response


@json_response
def sent_push_notifications(request, region_slug, language_slug):
    """
    Function to iterate through all sent push notifications related to a region and adds them to a JSON.

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str

    :return: JSON object according to APIv3 push notifications definition
    :rtype: ~django.http.JsonResponse
    """

    channel = request.GET.get("channel", "all")
    query_result = (
        PushNotificationTranslation.objects.filter(
            push_notification__region__slug=region_slug
        )
        .filter(push_notification__sent_date__isnull=False)
        .filter(language__slug=language_slug)
        .order_by("-last_updated")
    )
    if channel != "all":
        query_result = query_result.filter(push_notification__channel=channel)
    result = list(map(transform_notification, query_result))
    return JsonResponse(result, safe=False)


def transform_notification(pnt):
    """
    Function to create a JSON from a single push notification translation Object.

    :param pnt: A push notification translation
    :type pnt: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation

    :return: data necessary for API
    :rtype: dict
    """
    return {
        "id": str(pnt.pk),
        "title": pnt.title,
        "message": pnt.text,
        "timestamp": date_format(localtime(pnt.last_updated), "Y-m-d H:i:s"),
        "channel": pnt.push_notification.channel,
    }
