"""
This is a collection of tags and filters for :class:`~integreat_cms.cms.models.push_notifications.push_notification.PushNotification`
objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from ..models import PushNotification, PushNotificationTranslation

register = template.Library()


@register.simple_tag
def get_translation(
    push_notification: PushNotification, language_slug: str
) -> PushNotificationTranslation:
    """
    This tag returns the most recent translation of the requested push notification in the requested language.

    :param push_notification: The requested push notification
    :param language_slug: The slug of the requested language
    :return: The push notification translation
    """
    return push_notification.translations.filter(language__slug=language_slug).first()
