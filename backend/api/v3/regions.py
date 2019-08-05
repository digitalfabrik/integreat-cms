from django.db.models import Exists, OuterRef
from django.http import JsonResponse, HttpResponse

from cms.models import Region, Extra, Language

PREFIXES = [
    'EAE',
    'Landkreis',
    'Kreis',
    'Stadt',
]

def strip_prefix(name):
    for p in PREFIXES:
        if name.startswith(p):
            return p, name[len(p) + 1:]  # +1 for one whitespace
    return None, name

def transform_region(s):
    prefix, name_without_prefix = strip_prefix(s.name)
    return {
        'id': s.id,
        'name': s.name,
        'path': s.slug,
        'live': s.status == Region.ACTIVE,
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

def transform_region_by_status(s):
    prefix, name_without_prefix = strip_prefix(s.name)
    return {
        'id': s.id,
        'name': s.name,
        'path': s.slug,
        'prefix': prefix,
        'name_without_prefix': name_without_prefix,
        'plz': s.postal_code,
        'extras': s.extras_enabled,
        'events': s.events_enabled,
        'push-notifications': s.push_notifications_enabled,
    }

def regions(_):
    result = list(map(transform_region,
                      Region.objects.exclude(status=Region.ARCHIVED)
                      .annotate(extras_enabled=Exists(Extra.objects.filter(region=OuterRef('pk'))))
                      ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays

def liveregions(_):
    result = list(map(transform_region_by_status,
                      Region.objects.filter(status=Region.ACTIVE)
                      .annotate(extras_enabled=Exists(Extra.objects.filter(region=OuterRef('pk'))))
                      ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays

def hiddenregions(_):
    result = list(map(transform_region_by_status,
                      Region.objects.filter(status=Region.HIDDEN)
                      .annotate(extras_enabled=Exists(Extra.objects.filter(region=OuterRef('pk'))))
                      ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays

def pushnew(_):
    """
    This is a convenience function for development.
    todo: To be removed on deploy.
    """
    de = Language(code='de', title='Deutsch', text_direction='ltr')
    dutch = Language(code='nl', title='Nederlands', text_direction='ltr')
    de.save()
    dutch.save()
    region = Region(
        title='Augsburg',
        name='augsburg',
        languages=[de, dutch],
        push_notification_channels=[]
    )
    region.save()
    return HttpResponse('Pushing successful')
