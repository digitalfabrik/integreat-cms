from django.db import models
from django.utils import timezone


class PushNotificationTranslation(models.Model):
    """
    Data model representing a push notification translation

    :param id: The database id of the push notification translation
    :param title: The title of the push notification translation
    :param text: The content of the push notification translation
    :param created_date: The date and time when the push notification translation was created
    :param last_updated: The date and time when the push notification translation was last updated

    Relationship fields:

    :param push_notification: The push notification the translation belongs to (related name: ``translations``)
    :param language: The language of the push notification translation (related name:
                     ``push_notification_translations``)
    """

    title = models.CharField(max_length=250)
    text = models.CharField(max_length=250)
    language = models.ForeignKey('Language', related_name='push_notification_translations', on_delete=models.CASCADE)
    push_notification = models.ForeignKey('PushNotification', related_name='translations', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <PushNotificationTranslation object at 0xDEADBEEF>

        :return: The string representation (in this case the title) of the push notification translation
        :rtype: str
        """
        return self.title

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """
        default_permissions = ()
