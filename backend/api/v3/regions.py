from django.db.models import Exists, OuterRef
from django.http import JsonResponse, HttpResponse

from cms.models import Region, Offer, Language
from cms.constants import region_status


def transform_region(region):
    return {
        'id': region.id,
        'name': region.get_administrative_division_display() + ' ' + region.name,
        'path': region.slug,
        'live': region.status == region_status.ACTIVE,
        'prefix': region.get_administrative_division_display(),
        'name_without_prefix': region.name,
        'plz': region.postal_code,
        'offers': region.offers_enabled,
        'events': region.events_enabled,
        'push-notifications': region.push_notifications_enabled,
        'longitude': region.longitude,
        'langitude': region.latitude,
        'aliases': region.aliases,
    }

def transform_region_by_status(region):
    return {
        'id': region.id,
        'name': region.get_administrative_division_display() + ' ' + region.name,
        'path': region.slug,
        'prefix': region.get_administrative_division_display(),
        'name_without_prefix': region.name,
        'plz': region.postal_code,
        'offers': region.offers_enabled,
        'events': region.events_enabled,
        'push-notifications': region.push_notifications_enabled,
        'longitude': region.longitude,
        'langitude': region.latitude,
        'aliases': region.aliases,
    }

def regions(_):
    result = list(map(
        transform_region,
        Region.objects.exclude(status=region_status.ARCHIVED).annotate(offers_enabled=Exists(Offer.objects.filter(region=OuterRef('pk'))))
    ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays

def liveregions(_):
    result = list(map(
        transform_region_by_status,
        Region.objects.filter(status=region_status.ACTIVE).annotate(offers_enabled=Exists(Offer.objects.filter(region=OuterRef('pk'))))
    ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays

def hiddenregions(_):
    result = list(map(
        transform_region_by_status,
        Region.objects.filter(status=region_status.HIDDEN).annotate(offers_enabled=Exists(Offer.objects.filter(region=OuterRef('pk'))))
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
