"""
Retrieve push notifications that have been sent, optionally filtering by channel.
"""
from django.http import JsonResponse

from cms.models import PushNotificationTranslation


def sent_push_notifications(req, region_slug, lan_code):
    channel = req.GET.get('channel', 'all')
    query_result = PushNotificationTranslation.objects \
        .filter(push_notification__region__slug=region_slug) \
        .filter(push_notification__sent_date__isnull=False) \
        .filter(language__code=lan_code)
    if channel != 'all':
        query_result = query_result.filter(push_notification__channel=channel)
    result = list(map(transform_notification, query_result))
    return JsonResponse(result, safe=False)


def transform_notification(pn):
    return {'title': pn.title, 'text': pn.text, 'channel': pn.push_notification.channel,
            'sent_date': pn.push_notification.sent_date}
