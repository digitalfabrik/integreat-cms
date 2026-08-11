from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import F
from django.db.models.functions import Greatest
from django.http import Http404, JsonResponse
from django.utils import timezone

from ..cms.models import PushNotificationTranslation
from ..cms.utils.social_media_utils import (
    get_excerpt,
    get_region_title,
    render_social_media_headers,
)
from .abstract_news_manager import AbstractNewsManager, NewsItem

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet
    from django.http import HttpRequest, HttpResponse

    from ..cms.models import Language, Region


def _query_sent_translations(
    region_slug: str, language_slug: str, channel: str
) -> QuerySet:
    """
    Collect all sent push notification translations in ``region_slug`` and
    ``language_slug`` whose sent date is within the FCM history window.
    """
    query_result = (
        PushNotificationTranslation.objects.filter(push_notification__archived=False)
        .filter(push_notification__regions__slug=region_slug)
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


class PushnewsManager(AbstractNewsManager):
    short_name = "local"
    name = "Local News"

    def import_news_items(self) -> None:
        """
        Push notifications live in our own database, so there is nothing to import.
        """
        return

    def collect_news_items(
        self, region_slug: str, language_slug: str, channel: str
    ) -> list[NewsItem]:
        """
        Returns push notification news for common news endpoint
        """
        query_result = _query_sent_translations(region_slug, language_slug, channel)
        return list(map(self.transform_notification, query_result))

    def social_media_headers(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_raw_id: str,
    ) -> HttpResponse:
        """
        Tries rendering the social media headers for a news page in a specified region and language
        """
        if not (
            pn_translation := PushNotificationTranslation.objects.filter(
                language__slug=language.slug,
                push_notification__id=news_raw_id,
                push_notification__regions=region,
            ).first()
        ):
            raise Http404(
                "Push Notification not found in this region with this language."
            )

        return render_social_media_headers(
            request=request,
            title=get_region_title(region, pn_translation.get_title()),
            language_code=language.bcp47_tag,
            excerpt=get_excerpt(pn_translation.get_text()),
            url=f"{settings.WEBAPP_URL}{pn_translation.get_absolute_url()}",
        )

    def get_single_news(
        self,
        request: HttpRequest,
        region: Region,
        language: Language,
        news_id: str,
    ) -> JsonResponse:
        """
        Returns a push notification that matches the id
        """
        if not (
            pn_translation := PushNotificationTranslation.objects.filter(
                language__slug=language.slug,
                id=news_id,
                push_notification__regions=region,
            )
            .filter(push_notification__archived=False)
            .filter(
                push_notification__sent_date__gte=timezone.now()
                - timezone.timedelta(days=settings.FCM_HISTORY_DAYS),
            )
            .annotate(
                display_date=Greatest(
                    F("last_updated"), F("push_notification__sent_date")
                )
            )
            .first()
        ):
            raise Http404(
                "Push Notification not found in this region with this language."
            )

        return JsonResponse(self.transform_notification(pn_translation), safe=False)

    def collect_news_items_for_fcm(
        self, region_slug: str, language_slug: str, channel: str
    ) -> list[dict[str, Any]]:
        """
        Returns push notification news for `fcm` endpoint
        """
        query_result = _query_sent_translations(region_slug, language_slug, channel)
        return list(map(self.transform_notification_for_fcm, query_result))

    def transform_notification(self, pnt: PushNotificationTranslation) -> NewsItem:
        """
        Function to create a JSON from a single push notification translation Object.

        :param pnt: A push notification translation
        :return: data necessary for API
        """
        available_languages_dict = {
            translation.language.slug: {"id": f"{self.short_name}-{translation.id}"}
            for translation in pnt.push_notification.translations.all()
        }
        return {
            "id": f"{self.short_name}-{pnt.pk!s}",
            "title": pnt.get_title(),
            "content": pnt.get_text(),
            "last_updated": timezone.localtime(pnt.last_updated),
            "published_at": timezone.localtime(
                pnt.push_notification.sent_date or pnt.last_updated,
            ),
            "display_date": pnt.display_date,
            "channel": pnt.push_notification.channel,
            "available_languages": available_languages_dict,
            "source": self.short_name,
            "externalUrl": f"{settings.WEBAPP_URL}{pnt.get_absolute_url()}",
        }

    def transform_notification_for_fcm(
        self, pnt: PushNotificationTranslation
    ) -> dict[str, Any]:
        """
        Function to create a JSON from a single push notification translation Object for `fcm` endpoint

        The endpoint `fcm/` requires timestamp and id in int.

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
            "published_at": timezone.localtime(
                pnt.push_notification.sent_date or pnt.last_updated,
            ),
            "display_date": pnt.display_date,
            "channel": pnt.push_notification.channel,
            "available_languages": available_languages_dict,
        }
