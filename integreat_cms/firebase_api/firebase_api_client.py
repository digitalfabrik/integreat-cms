from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import google.auth
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.oauth2 import service_account
from requests.exceptions import RequestException

from ..cms.constants import push_notifications as pnt_const
from ..cms.forms.push_notifications.push_notification_translation_form import (
    PushNotificationTranslation,
)
from ..cms.models import Region

if TYPE_CHECKING:
    from ..cms.models.push_notifications.push_notification import PushNotification

logger = logging.getLogger(__name__)


class FirebaseApiClient:
    """
    Firebase Push Notifications / Firebase Cloud Messaging

    Sends push notifications via FCM HTTP API.
    Definition: https://firebase.google.com/docs/cloud-messaging/http-server-ref#downstream-http-messages-json

    .. warning::

        We use legacy HTTP-API - Migration to HTTP v1-API will be necessary!
        https://firebase.google.com/docs/cloud-messaging/migrate-v1
    """

    def __init__(self, push_notification: PushNotification) -> None:
        """
        Load relevant push notification translations and prepare content for sending

        :param push_notification: the push notification that should be sent
        :raises ~django.core.exceptions.ImproperlyConfigured: If the auth key is missing or the system runs in debug
                                                              mode but the test region does not exist.
        """
        self.push_notification = push_notification
        self.fcm_url = settings.FCM_URL
        self.prepared_pnts = []
        self.primary_pnt = PushNotificationTranslation.objects.get(
            push_notification=push_notification,
            language=push_notification.default_language,
        )
        if self.primary_pnt.title:
            self.prepared_pnts.append(self.primary_pnt)
        self.load_secondary_pnts()

        if not settings.FCM_ENABLED:
            raise ImproperlyConfigured("Push notifications are disabled")

        if settings.DEBUG:
            # Prevent sending PNs to actual users in development
            try:
                self.regions = [Region.objects.get(slug=settings.TEST_REGION_SLUG)]
            except Region.DoesNotExist as e:
                raise ImproperlyConfigured(
                    f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
                ) from e
        else:
            self.regions = push_notification.regions.all()

    def load_secondary_pnts(self) -> None:
        """
        Load push notification translations in other languages
        """
        secondary_pnts = PushNotificationTranslation.objects.filter(
            push_notification=self.push_notification
        ).exclude(id=self.primary_pnt.id)
        for secondary_pnt in secondary_pnts:
            if (
                not secondary_pnt.title
                and pnt_const.USE_MAIN_LANGUAGE == self.push_notification.mode
            ):
                secondary_pnt.title = self.primary_pnt.title
                secondary_pnt.text = self.primary_pnt.text
                self.prepared_pnts.append(secondary_pnt)
            elif len(secondary_pnt.title) > 0:
                self.prepared_pnts.append(secondary_pnt)

    def is_valid(self) -> bool:
        """
        Check if all data for sending push notifications is available

        :return: all prepared push notification translations are valid
        """
        if not self.prepared_pnts:
            logger.debug(
                "%r does not have a default translation", self.push_notification
            )
            return False
        for pnt in self.prepared_pnts:
            if not pnt.title:
                logger.debug("%r has no title", pnt)
                return False
        return True

    def send_pn(self, pnt: PushNotificationTranslation, region: Region) -> bool:
        """
        Send single push notification translation

        :param pnt: The prepared push notification translation to be sent
        :param region: The region for which to send the prepared push notification translation
        :return: whether the push notification was sent successfully
        """
        # In debug mode, pass `validate_only`: True, to avoid messages actually being sent
        payload = {
            "validate_only": settings.DEBUG,
            "message": {
                "topic": f"{region.slug}-{pnt.language.slug}-{self.push_notification.channel}",
                "notification": {"title": pnt.title, "body": pnt.text},
                "data": {
                    "news_id": str(pnt.id),
                    "city_code": region.slug,
                    "language_code": pnt.language.slug,
                    "group": self.push_notification.channel,
                },
                "apns": {
                    "headers": {"apns-priority": "5"},
                    "payload": {
                        "aps": {
                            "category": "NEW_MESSAGE_CATEGORY",
                        }
                    },
                },
                "android": {
                    "ttl": "86400s",
                },
                "fcm_options": {
                    "analytics_label": f"{region.slug}-{pnt.language.slug}"
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json; UTF-8",
        }

        try:
            response = requests.post(
                self.fcm_url,
                json=payload,
                headers=headers,
                timeout=settings.DEFAULT_REQUEST_TIMEOUT,
            )
            if response.status_code == 200 and response.json().get("name"):
                logger.info("%r sent, FCM id: %r", pnt, response.json().get("name"))
                return True

            logger.warning(
                "%r sent, but unexpected API response: %r",
                pnt,
                response.json(),
            )
            return False
        except RequestException as e:
            logger.error(e)
            return False

    def send_all(self) -> bool:
        """
        Send all prepared push notification translations

        :return: Success status
        """
        status = True
        for pnt in self.prepared_pnts:
            for region in self.regions:
                if pnt.language in region.active_languages:
                    if not self.send_pn(pnt, region):
                        status = False
        return status

    @staticmethod
    def _get_access_token() -> str:
        """
        Retrieve a valid access token that can be used to authorize requests.
        This function is taken from https://github.com/firebase/quickstart-python/blob/2c68e7c5020f4dbb072cca4da03dba389fbbe4ec/messaging/messaging.py#L26-L35

        :return: Access token
        """
        credentials = service_account.Credentials.from_service_account_file(
            settings.FCM_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
