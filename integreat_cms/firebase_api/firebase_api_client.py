import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..cms.constants import push_notifications as pnt_const
from ..cms.forms.push_notifications.push_notification_translation_form import (
    PushNotificationTranslation,
)
from ..cms.models import Region

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

    def __init__(self, push_notification):
        """
        Load relevant push notification translations and prepare content for sending

        :param push_notification: the push notification that should be sent
        :type push_notification: ~integreat_cms.cms.models.push_notifications.push_notification.PushNotification

        :raises ~django.core.exceptions.ImproperlyConfigured: If the auth key is missing or the system runs in debug
                                                              mode but the test region does not exist.
        """
        self.push_notification = push_notification
        self.fcm_url = settings.FCM_URL
        self.prepared_pnts = []
        self.primary_pnt = PushNotificationTranslation.objects.get(
            push_notification=push_notification,
            language=push_notification.regions.first().default_language,
        )
        if self.primary_pnt.title:
            self.prepared_pnts.append(self.primary_pnt)
        self.load_secondary_pnts()

        if not settings.FCM_ENABLED:
            raise ImproperlyConfigured("Push notifications are disabled")
        self.auth_key = settings.FCM_KEY

        if settings.DEBUG:
            # Prevent sending PNs to actual users in development
            try:
                self.region = Region.objects.get(slug=settings.TEST_REGION_SLUG)
            except Region.DoesNotExist as e:
                raise ImproperlyConfigured(
                    f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
                ) from e
        self.regions = push_notification.regions.all()

    def load_secondary_pnts(self):
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

    def is_valid(self):
        """
        Check if all data for sending push notifications is available

        :return: all prepared push notification translations are valid
        :rtype: bool
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

    def send_pn(self, pnt, region):
        """
        Send single push notification translation

        :param pnt: The prepared push notification translation to be sent
        :type pnt: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation

        :param region: The region for which to send the prepared push notification translation
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :return: Response of the :mod:`requests` library
        :rtype: ~requests.Response
        """
        payload = {
            "to": f"/topics/{region.slug}-{pnt.language.slug}-{self.push_notification.channel}",
            "notification": {"title": pnt.title, "body": pnt.text},
            "data": {
                "news_id": str(pnt.id),
                "city_code": region.slug,
                "language_code": pnt.language.slug,
                "group": self.push_notification.channel,
            },
            "apns": {
                "headers": {"apns-priority": "5"},
            },
            "android": {
                "ttl": "86400s",
            },
            "payload": {
                "aps": {
                    "category": "NEW_MESSAGE_CATEGORY",
                }
            },
        }
        headers = {"Authorization": f"key={self.auth_key}"}
        return requests.post(
            self.fcm_url,
            json=payload,
            headers=headers,
            timeout=settings.DEFAULT_REQUEST_TIMEOUT,
        )

    def send_all(self):
        """
        Send all prepared push notification translations

        :return: Success status
        :rtype: bool
        """
        status = True
        for pnt in self.prepared_pnts:
            for region in self.regions:
                if pnt.language in region.active_languages:
                    res = self.send_pn(pnt, region)
                    if res.status_code == 200:
                        if "message_id" in res.json():
                            logger.info(
                                "%r sent, FCM id: %r", pnt, res.json()["message_id"]
                            )
                        else:
                            logger.warning(
                                "%r sent, but unexpected API response: %r",
                                pnt,
                                res.json(),
                            )
                    else:
                        status = False
                        logger.error(
                            "Received invalid response from FCM for %r, status: %r, body: %r",
                            pnt,
                            res.status_code,
                            res.text,
                        )
        return status
