from django.http import JsonResponse

from cms.models import Region
from cms.constants import region_status


def transform_region(region):
    return {
        'id': region.id,
        'name': region.name,
        'path': region.slug,
        'administrative_division': region.get_administrative_division_display(),
        'postal_code': region.postal_code,
        'longitude': region.longitude,
        'langitude': region.latitude,
    }

def regions(_):
    result = list(map(
        transform_region,
        Region.objects.filter(status=region_status.ACTIVE)
    ))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays
