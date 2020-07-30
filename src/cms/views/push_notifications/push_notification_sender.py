import logging
import requests

from ...models import Configuration


# pylint: disable=too-few-public-methods
class PushNotificationSender:
    logger = logging.getLogger(__name__)
    fcm_url = "https://fcm.googleapis.com/fcm/send"

    """
    Sends push notifications via FCM legacy http api.
    Returns boolean indicating success or failure
    """

    # pylint: disable=too-many-arguments
    def send(self, region_slug, channel, title, message, lan_code):
        fcm_auth_config_key = "fcm_auth_key"
        auth_key = Configuration.objects.filter(key=fcm_auth_config_key)
        if auth_key.exists():
            self.logger.info("Got fcm_auth_key from database")
        else:
            self.logger.info(
                "Could not get %s from configuration database.", fcm_auth_config_key
            )
            return False
        payload = {
            "to": f"/topics/{region_slug}-{lan_code}-{channel}",
            "notification": {"title": title, "body": message},
            "data": {"lanCode": lan_code, "city": region_slug},
        }
        headers = {"Authorization": f"key={auth_key.first().value}"}
        res = requests.post(self.fcm_url, json=payload, headers=headers)
        if res.status_code == 200:
            self.logger.info("Message sent, id: %s", res.json()["message_id"])
            return True
        self.logger.info(
            "Received invalid response from FCM for push notification: %s, response body: %s",
            res.status_code,
            res.text,
        )
        return False
