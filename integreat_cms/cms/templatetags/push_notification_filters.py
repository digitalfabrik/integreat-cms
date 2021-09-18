"""
This is a collection of tags and filters for :class:`~integreat_cms.cms.models.push_notifications.push_notification.PushNotification`
objects.
"""
from django import template

register = template.Library()


@register.filter
def translation(push_notification, language):
    """
    This tag returns the most recent translation of the requested push notification in the requested language.

    :param push_notification: The requested push notification
    :type push_notification: ~integreat_cms.cms.models.push_notifications.push_notification.PushNotification

    :param language: The requested language
    :type language: ~integreat_cms.cms.models.languages.language.Language

    :return: The push notification translation
    :rtype: ~integreat_cms.cms.models.push_notifications.push_notification_translation.PushNotificationTranslation
    """
    return push_notification.translations.filter(language=language).first()
