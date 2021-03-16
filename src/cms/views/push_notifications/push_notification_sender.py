"""
Module for sending Push Notifications
"""
import logging
import requests

from django.conf import settings

from ...models import Configuration
from ...models import PushNotificationTranslation
from ...models import Region
from ...constants import push_notifications as pnt_const

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
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
        :type push_notification: ~cms.models.push_notifications.push_notification.PushNotification
        """
        self.push_notification = push_notification
        self.prepared_pnts = []
        self.primary_pnt = PushNotificationTranslation.objects.get(
            push_notification=push_notification,
            language=push_notification.region.default_language,
        )
        if len(self.primary_pnt.title) > 0:
            self.prepared_pnts.append(self.primary_pnt)
        self.load_secondary_pnts()
        self.auth_key = self.get_auth_key()

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
            if len(secondary_pnt.title) > 0:
                self.prepared_pnts.append(secondary_pnt)

    def is_valid(self):
        """
        Check if all data for sending push notifications is available

        :return: all prepared push notification translations are valid
        :rtype: bool
        """
        if self.auth_key is None:
            return False
        for pnt in self.prepared_pnts:
            if not pnt.title:
                logger.debug("%r has no title", pnt)
                return False
        return True

    @staticmethod
    def get_auth_key():
        """
        Get FCM API auth key

        :return: FCM API auth key
        :rtype: str
        """
        fcm_auth_config_key = "fcm_auth_key"
        auth_key = Configuration.objects.filter(key=fcm_auth_config_key)
        if auth_key.exists():
            logger.debug("Got fcm_auth_key from database")
            return auth_key.first().value
        logger.warning(
            "Could not get %r from configuration database", fcm_auth_config_key
        )
        return None

    def send_pn(self, pnt):
        """
        Send single push notification translation

        :param pnt: the prepared push notification translation to be sent
        :type pnt: ~cms.models.push_notifications.push_notification_translation.PushNotificationTranslation

        :return: Response of the :mod:`requests` library
        :rtype: ~requests.Response
        """
        if settings.DEBUG:
            region_slug = Region.objects.get(
                id=settings.TEST_BLOG_ID
            ).slug  # Testumgebung - prevent sending PNs to actual users in development
        else:
            region_slug = self.push_notification.region.slug
        payload = {
            "to": f"/topics/{region_slug}-{pnt.language.slug}-{self.push_notification.channel}",
            "notification": {"title": pnt.title, "body": pnt.text},
            "data": {
                "lanCode": pnt.language.slug,
                "city": self.push_notification.region.slug,
            },
        }
        headers = {"Authorization": f"key={self.auth_key}"}
        return requests.post(self.fcm_url, json=payload, headers=headers)

    # pylint: disable=too-many-arguments
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
                logger.info("%r sent, FCM id: %r", pnt, res.json()["message_id"])
            else:
                status = False
                logger.warning(
                    "Received invalid response from FCM for %r, status: %r, body: %r",
                    pnt,
                    res.status_code,
                    res.text,
                )
        return status
