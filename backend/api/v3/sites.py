from django.db.models import Exists, OuterRef
from django.http import JsonResponse, HttpResponse

from cms.models import Site, Extra, ExtraTemplate, Language

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

    result = list(map(transform_site,
                      Site.objects.exclude(status=Site.ARCHIVED)
                      .annotate(extras_enabled=Exists(Extra.objects.filter(site=OuterRef('pk'))))
                      ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays


def pushnew(_):
    """
    This is a convenience function for development.
    todo: To be removed on deploy.
    """
    en = Language()
    en.code = 'es'
    en.title = 'English'
    en.text_direction = 'ltr'
    en.save()

    template = ExtraTemplate()
    template.save()
    site = Site()
    site.push_notification_channels = []
    site.latitude = 48.37154
    site.longitude = 10.89851
    site.name = 'augsburg223'
    site.title = 'Stadt Augsburg'
    site.save()
    site.supported_languages = [en]
    site.save()

    extra = Extra()
    extra.template = template
    extra.site = site
    extra.save()
    return HttpResponse('Pushing successful')
