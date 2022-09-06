"""
Module for sending Push Notifications
"""
import logging
import requests

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..models import PushNotificationTranslation
from ..models import Region
from ..constants import push_notifications as pnt_const

logger = logging.getLogger(__name__)


class PushNotificationSender:
    """
    Sends push notifications via FCM HTTP API.
    Definition: https://firebase.google.com/docs/cloud-messaging/http-server-ref#downstream-http-messages-json
    """

    fcm_url = "https://fcm.googleapis.com/fcm/send"

    def __init__(self, push_notification):
        """
        Load relevant push notification translations and prepare content for sending

        :param push_notification: the push notification that should be sent
        :type push_notification: ~integreat_cms.cms.models.push_notifications.push_notification.PushNotification

        :raises ~django.core.exceptions.ImproperlyConfigured: If the auth key is missing or the system runs in debug
                                                              mode but the test region does not exist.
        """
        self.push_notification = push_notification
        self.prepared_pnts = []
        self.primary_pnt = PushNotificationTranslation.objects.get(
            push_notification=push_notification,
            language=push_notification.region.default_language,
        )
        if self.primary_pnt.title:
            self.prepared_pnts.append(self.primary_pnt)
        self.load_secondary_pnts()

        if not settings.FCM_ENABLED:
            raise ImproperlyConfigured("Push notifications are disabled")
        self.auth_key = settings.FCM_KEY

        if settings.DEBUG:
            # Prevent sending PNs to actual users in development
            test_region = Region.objects.filter(slug=settings.TEST_REGION_SLUG).first()
            if not test_region:
                raise ImproperlyConfigured(
                    f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
                )
            self.region = test_region
        self.region = push_notification.region

    def load_secondary_pnts(self):
        """
        Load push notification translations in other languages
        """
        secondary_pnts = PushNotificationTranslation.objects.filter(
            push_notification=self.push_notification
        ).exclude(id=self.primary_pnt.id)
        for secondary_pnt in secondary_pnts:
            if (
                secondary_pnt.title == ""
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

    def send_pn(self, pnt):
        """
        Send single push notification translation

        :param pnt: the prepared push notification translation to be sent
        :type pnt: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation

        :return: Response of the :mod:`requests` library
        :rtype: ~requests.Response
        """
        payload = {
            "to": f"/topics/{self.region.slug}-{pnt.language.slug}-{self.push_notification.channel}",
            "notification": {"title": pnt.title, "body": pnt.text},
            "data": {
                "news_id": str(pnt.id),
                "city_code": self.region.slug,
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
            res = self.send_pn(pnt)
            if res.status_code == 200:
                if "message_id" in res.json():
                    logger.info("%r sent, FCM id: %r", pnt, res.json()["message_id"])
                else:
                    logger.warning(
                        "%r sent, but unexpected API response: %r", pnt, res.json()
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
