"""
This module includes functions related to the push notification that are sent via firebase.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import F
from django.db.models.functions import Greatest
from django.http import JsonResponse
from django.utils import timezone

from ...cms.models import NewsItem, PushNotificationTranslation, Region
from ..decorators import json_response

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet
    from django.http import HttpRequest


def collect_sent_push_notifications(
    region_slug: str, language_slug: str, channel: str
) -> QuerySet:
    """
    Function to collect all sent push notifications related to a region
    """
    query_result = (
        PushNotificationTranslation.objects.filter(push_notification__archived=False)
        .filter(
            push_notification__regions__slug=region_slug,
        )
        .filter(
            push_notification__sent_date__gte=timezone.now()
            - timezone.timedelta(days=settings.FCM_HISTORY_DAYS),
        )
        .filter(language__slug=language_slug)
        .annotate(
            display_date=Greatest(F("last_updated"), F("push_notification__sent_date"))
        )
        .order_by("-display_date")
    )
    if channel != "all":
        query_result = query_result.filter(push_notification__channel=channel)
    return query_result


def collect_tue_news(region_slug: str, language_slug: str) -> QuerySet:
    """
    Function to collect all sent push notifications related to a region
    """
    if not Region.objects.get(slug=region_slug).external_news_enabled:
        return ()

    return NewsItem.objects.filter(
        pub_date__gte=timezone.now()
        - timezone.timedelta(days=settings.FCM_HISTORY_DAYS)
    ).filter(language__code=language_slug)


@json_response
def sent_push_notifications(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Function to iterate through all sent push notifications related to a region and adds them to a JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON object according to APIv3 push notifications definition
    """
    channel = request.GET.get("channel", "all")
    query_result = collect_sent_push_notifications(region_slug, language_slug, channel)

    result = list(map(transform_notification, query_result))
    return JsonResponse(result, safe=False)


@json_response
def all_news(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
) -> JsonResponse:
    """
    Function to iterate through all sent push notifications related to a region and news from Tü News, and adds them to a JSON.

    :param request: Django request
    :param region_slug: slug of a region
    :param language_slug: language slug
    :return: JSON object according to APIv3 push notifications definition
    """
    channel = request.GET.get("channel", "all")

    sent_push_notifications = collect_sent_push_notifications(
        region_slug, language_slug, channel
    )

    tu_news = collect_tue_news(region_slug, language_slug)

    result = list(map(transform_notification, sent_push_notifications)) + list(
        map(transform_tue_news, tu_news)
    )

    return JsonResponse(result, safe=False)


def transform_notification(pnt: PushNotificationTranslation) -> dict[str, Any]:
    """
    Function to create a JSON from a single push notification translation Object.

    :param pnt: A push notification translation
    :return: data necessary for API
    """
    available_languages_dict = {
        translation.language.slug: {"id": translation.id}
        for translation in pnt.push_notification.translations.all()
    }
    return {
        "id": pnt.pk,
        "title": pnt.get_title(),
        "message": pnt.get_text(),
        "timestamp": pnt.last_updated,  # deprecated field in the future
        "last_updated": timezone.localtime(pnt.last_updated),
        "display_date": pnt.display_date,
        "channel": pnt.push_notification.channel,
        "available_languages": available_languages_dict,
    }


def transform_tue_news(news: NewsItem) -> dict[str, Any]:
    """
    Function to create a JSON from a single Tü News item tObject.

    :param pnt: A push notification translation
    :return: data necessary for API
    """
    available_languages_dict = {
        language_slug: {"id": post_id}
        for language_slug, post_id in json.loads(str(news.translations)).items()
    }
    return {
        "id": news.pk,
        "title": news.title,
        "message": news.content,
        "timestamp": news.pub_date,  # deprecated field in the future
        "last_updated": news.pub_date,
        "display_date": news.pub_date,
        "channel": news.newscategory.name,
        "available_languages": available_languages_dict,
    }
