from django import template

register = template.Library()

@register.filter
def translation(push_notification, language):
    return push_notification.translations.filter(language=language).first()
