import requests
import logging

from ...models.configuration import Configuration


class PushNotificationSender:
    logger = logging.getLogger(__name__)
    fcm_url = "https://fcm.googleapis.com/fcm/send"

    """
    Sends push notifications via FCM legacy http api.  
    Returns boolean indicating success or failure
    """

    def send(self, site_slug, channel, title, message, lan_code):
        fcm_auth_config_key = 'fcm_auth_key'
        auth_key = Configuration.objects.filter(key=fcm_auth_config_key)
        if auth_key.exists():
            self.logger.info("Got fcm_auth_key from database")
        else:
            self.logger.info("Could not get {} from configuration database.",
                             fcm_auth_config_key)
            return False
        payload = {'to': '/topics/{}-{}-{}'.format(site_slug, lan_code, channel),
                   'notification': {
                       'title': title,
                       'body': message
                   },
                   'data': {'lanCode': lan_code, 'city': site_slug}
                   }
        headers = {'Authorization': 'key={}'.format(auth_key.first().value)}
        res = requests.post(self.fcm_url, json=payload, headers=headers)
        if res.status_code == 200:
            self.logger.info("Message sent, id: {}", res.json()['message_id'])
            return True
        else:
            self.logger.info("Received invalid response from FCM for push notification: {}, response body: {}",
                             res.status_code, res.text)
            return False
