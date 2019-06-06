import requests
import logging

from ...models.configuration import Configuration


class PushNotificationSender:
    logger = logging.getLogger(__name__)
    fcm_url = "https://fcm.googleapis.com/fcm/send"

    def __init__(self):
        fcm_auth_config_key = 'fcm_auth_key'
        auth_key = Configuration.objects.get(key=fcm_auth_config_key)
        self.headers = {'Authorization': 'key={}'.format(auth_key.value)}

    """
    Sends push notifications via FCM legacy http api.  
    Returns boolean indicating success or failure
    """

    def send(self, site_slug, channel, title, message, lan_code):
        payload = {'to': '/topics/{}-{}-{}'.format(site_slug, lan_code, channel),
                   'notification': {
                       'title': title,
                       'body': message
                   },
                   'data': {'lanCode': lan_code, 'city': site_slug}
                   }
        res = requests.post(self.fcm_url, json=payload, headers=self.headers)
        if res.status_code == 200:
            self.logger.info("Message sent, id: {}", res.json()['message_id'])
            return True
        else:
            self.logger.info("Received invalid response from FCM for push notification: {}, response body: {}",
                             res.status_code, res.text)
            return False
