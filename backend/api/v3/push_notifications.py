from django.http import JsonResponse

from cms.models import PushNotificationTranslation

"""
Retrieve push notifications that have been sent, optionally filtering by channel.
"""


def sent_push_notifications(req, site_slug, lan_code):
    channel = req.GET.get('channel', 'all')
    query_result = PushNotificationTranslation.objects \
        .filter(push_notification__site__slug=site_slug) \
        .filter(push_notification__sent_date__isnull=False) \
        .filter(language__code=lan_code)
    if channel != 'all':
        query_result = query_result.filter(push_notification__channel=channel)
    result = list(map(transform_notification, query_result))
    return JsonResponse(result, safe=False)


def transform_notification(pn):
    return {'title': pn.title, 'text': pn.text, 'channel': pn.push_notification.channel,
            'sent_date': pn.push_notification.sent_date}
