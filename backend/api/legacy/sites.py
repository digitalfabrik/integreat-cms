from django.http import JsonResponse, HttpResponse

from cms.models import Site

PREFIXES = [
    'EAE',
    'Landkreis',
    'Kreis',
    'Stadt',
]


def sites(_):
    def strip_prefix(title):
        for p in PREFIXES:
            if title.startswith(p):
                return p, title[len(p) + 1:]  # +1 for one whitespace
        return None, title

    def transform_site(s):
        prefix, name_without_prefix = strip_prefix(s.title)
        return {
            'id': s.name,
            'name': s.title,
            'path': f'/{s.name}/',  # todo: tbd
            'live': s.status == Site.ACTIVE,
            'prefix': prefix,
            'name_without_prefix': name_without_prefix,
            'plz': s.postal_code,
            'extras': s.extras_enabled,
            'events': s.events_enabled,
            'push-notifications': s.push_notifications_enabled,
            'longitude': s.longitude,
            'langitude': s.latitude,
            'aliases': None  # todo
        }

    result = list(map(transform_site, Site.objects.exclude(status=Site.ARCHIVED)))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays


def pushnew(_):
    """
    This is a convenience function for development.
    todo: To be removed on deploy.
    """
    site = Site()
    site.push_notification_channels = []
    site.latitude = 48.37154
    site.longitude = 10.89851
    site.name = 'augsburg'
    site.title = 'Stadt Augsburg'
    site.save()
    return HttpResponse('Pushing successful')
